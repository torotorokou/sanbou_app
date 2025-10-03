"""Interactive processing service.

ReportProcessingService のインタラクティブ版。

責務:
 - 初回: CSV 読込 / validate / (期間フィルタ) / format まで共通処理
 - generator.initial_step を呼び state/payload と session_data を返す
 - apply: 受け取った session_data を復元し generator.apply_step を呼ぶ
 - finalize: 復元 -> generator.finalize_step -> Excel/PDF 保存 & URL 返却
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, Union

from fastapi import UploadFile
from fastapi.responses import JSONResponse

from app.api.services.report.core.base_generators import (
    BaseInteractiveReportGenerator,
)
from app.api.services.report.core.processors.report_processing_service import ReportProcessingService
from app.api.services.report.session import session_store

# (NoFilesUploadedResponse, read_csv_files は base クラス経由で利用しないため削除)
from backend_shared.src.utils.date_filter_utils import (
    filter_by_period_from_min_date as shared_filter_by_period_from_min_date,
)


class InteractiveReportProcessingService(ReportProcessingService):
    """インタラクティブ帳票用サービス"""

    # 既存 _read_uploaded_files を再利用しても良いが、型が同一なのでそのまま呼ぶ

    # -------- Initial --------
    def initial(
        self, generator: BaseInteractiveReportGenerator, files: Dict[str, UploadFile]
    ) -> Dict[str, Any]:
        dfs, error = self._read_uploaded_files(files)
        if error:
            # エラーオブジェクトを可能な限り展開して返す
            try:
                if hasattr(error, "to_dict"):
                    return error.to_dict()
            except Exception:
                pass
            return {"status": "error", "message": str(error)}

        assert dfs is not None

        validation_error = generator.validate(dfs, files)
        if validation_error:
            # ErrorApiResponse 系なら内部 payload を dict 化して返す
            if hasattr(validation_error, "payload"):
                try:
                    from backend_shared.src.api_response.response_base import (
                        _model_to_dict,
                    )

                    return _model_to_dict(validation_error.payload)
                except Exception:
                    pass
            # フォールバック
            return {"status": "error", "message": str(validation_error)}

        period_type = getattr(generator, "period_type", None)
        if period_type:
            try:
                dfs = shared_filter_by_period_from_min_date(dfs, period_type)
            except Exception as e:  # noqa: BLE001
                print(f"[WARN] date filtering skipped: {e}")

        df_formatted = generator.format(dfs)

        state, payload = generator.initial_step(df_formatted)
        # state に元 df_formatted が必要なら利用側で含める方針 (明示性)

        preferred_session_id: Optional[str] = None
        state_session_id = state.get("session_id") if isinstance(state, dict) else None
        if isinstance(state_session_id, str) and state_session_id:
            preferred_session_id = state_session_id
        else:
            payload_session_id = (
                payload.get("session_id")
                if isinstance(payload, dict)
                else None
            )
            if isinstance(payload_session_id, str) and payload_session_id:
                preferred_session_id = payload_session_id

        session_data = generator.serialize_state(state)
        session_id = session_store.save(session_data, session_id=preferred_session_id)

        if session_id != preferred_session_id:
            # generator 側で採番した session_id と実際に保存された ID を揃える
            if isinstance(state, dict):
                state["session_id"] = session_id
            session_data = generator.serialize_state(state)
            session_store.save(session_data, session_id=session_id)

        payload = self._to_serializable(payload)
        if isinstance(payload, dict):
            payload["session_id"] = session_id

        if isinstance(payload, dict) and payload.get("status") == "error":
            return payload

        response_payload: Dict[str, Any] = {
            "session_id": session_id,
            "rows": payload.get("rows", []) if isinstance(payload, dict) else [],
        }

        return response_payload

    # -------- Apply (中間) --------
    def apply(
        self,
        generator: BaseInteractiveReportGenerator,
        session_data: Union[Dict[str, Any], str],
        user_input: Dict[str, Any],
    ) -> Dict[str, Any] | JSONResponse:
        try:
            state_payload, session_id = self._resolve_session(session_data)
            if state_payload is None:
                return {
                    "status": "error",
                    "code": "SESSION_NOT_FOUND",
                    "detail": "session data could not be resolved",
                }

            state = generator.deserialize_state(state_payload)
            state, payload = generator.apply_step(state, user_input)
            session_data_updated = generator.serialize_state(state)
            if session_id:
                session_store.save(session_data_updated, session_id=session_id)
            # If frontend requested automatic finalize, run finalize here and
            # return the final JSON response (artifact URLs) directly.
            if isinstance(user_input, dict) and user_input.get("auto_finalize"):
                try:
                    final_df, finalize_payload = generator.finalize_step(state)
                    try:
                        report_date = finalize_payload.get(
                            "report_date", generator.make_report_date({"result": final_df})
                        )
                    except Exception:  # noqa: BLE001
                        from datetime import datetime

                        report_date = datetime.now().date().isoformat()
                    extra_payload = self._to_serializable(finalize_payload)
                    response = self.create_response(
                        generator,
                        final_df,
                        report_date,
                        extra_payload=extra_payload if isinstance(extra_payload, dict) else None,
                    )
                    summary = finalize_payload.get("summary")
                    if isinstance(summary, dict):
                        for k, v in summary.items():
                            try:
                                response.headers[f"X-Summary-{k}"] = str(v)
                            except Exception:  # noqa: BLE001
                                pass
                    if session_id:
                        session_store.delete(session_id)
                    return response
                except Exception as e:  # noqa: BLE001
                    return JSONResponse(
                        status_code=500,
                        content={
                            "status": "error",
                            "code": "AUTO_FINALIZE_FAILED",
                            "detail": str(e),
                        },
                    )

            result: Dict[str, Any] = {
                "session_id": session_id or user_input.get("session_id"),
                "selection_summary": payload.get("selection_summary"),
                "message": payload.get("message", "applied"),
                "step": payload.get("step", 1),
            }

            return result
        except Exception as e:  # noqa: BLE001
            return {
                "status": "error",
                "code": "APPLY_FAILED",
                "detail": str(e),
            }

    # -------- Finalize --------
    def finalize(
        self,
        generator: BaseInteractiveReportGenerator,
        session_data: Union[Dict[str, Any], str],
        user_input: Optional[Dict[str, Any]] = None,
    ) -> JSONResponse:
        try:
            state_payload, session_id = self._resolve_session(session_data)
            if state_payload is None:
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "error",
                        "code": "SESSION_NOT_FOUND",
                        "detail": "session data could not be resolved",
                    },
                )

            state = generator.deserialize_state(state_payload)
            # ユーザー入力（selections 等）が渡された場合は finalize 前に適用
            if user_input and hasattr(generator, "finalize_with_optional_selections"):
                try:
                    final_df, payload = generator.finalize_with_optional_selections(state, user_input)  # type: ignore[attr-defined]
                except Exception as e:  # noqa: BLE001
                    return JSONResponse(
                        status_code=500,
                        content={
                            "status": "error",
                            "code": "FINALIZE_WITH_INPUT_FAILED",
                            "detail": str(e),
                        },
                    )
            else:
                final_df, payload = generator.finalize_step(state)
            try:
                report_date = payload.get(
                    "report_date", generator.make_report_date({"result": final_df})
                )
            except Exception as e:  # noqa: BLE001
                # Fallback to today if date extraction fails
                from datetime import datetime

                print(f"[WARN] report_date fallback due to: {e}")
                report_date = datetime.now().date().isoformat()

            extra_payload = self._to_serializable(payload)
            response = self.create_response(
                generator,
                final_df,
                report_date,
                extra_payload=extra_payload if isinstance(extra_payload, dict) else None,
            )
            summary = payload.get("summary")
            if isinstance(summary, dict):
                for k, v in summary.items():
                    try:
                        response.headers[f"X-Summary-{k}"] = str(v)
                    except Exception:  # noqa: BLE001
                        pass
            if session_id:
                session_store.delete(session_id)
            return response
        except Exception as e:  # noqa: BLE001
            # finalize は JSON 返却のためエラーレスポンスを明示的に返す
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "code": "FINALIZE_FAILED",
                    "detail": str(e),
                },
            )

    # -------- Helpers --------
    @classmethod
    def _to_serializable(cls, value: Any) -> Any:
        """Pydantic BaseModel やその配列を dict/list へ変換して返す"""

        if hasattr(value, "dict") and callable(value.dict):  # pydantic BaseModel 等
            try:
                return value.dict()
            except Exception:  # noqa: BLE001
                pass

        if isinstance(value, dict):
            return {k: cls._to_serializable(v) for k, v in value.items()}

        if isinstance(value, (list, tuple, set)):
            converted = [cls._to_serializable(v) for v in value]
            if isinstance(value, tuple):
                return tuple(converted)
            if isinstance(value, set):
                return converted
            return converted

        return value

    def _resolve_session(
        self, session_payload: Union[Dict[str, Any], str]
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Resolve the stored session data from various payload formats.

        Supports three patterns for backward compatibility:
            1. Raw serialized state dict (legacy behaviour)
            2. ``{"session_id": "..."}``
            3. Plain session id string
        """

        if isinstance(session_payload, dict):
            if "session_id" in session_payload and isinstance(session_payload["session_id"], str):
                session_id = session_payload["session_id"]
                stored = session_store.load(session_id)
                return stored, session_id
            # Legacy mode: the dict itself is the serialized state
            return session_payload, None

        if isinstance(session_payload, str):
            stored = session_store.load(session_payload)
            return stored, session_payload

        return None, None
