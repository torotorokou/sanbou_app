"""Interactive processing service.

ReportProcessingService のインタラクティブ版。

責務:
 - 初回: CSV 読込 / validate / (期間フィルタ) / format まで共通処理
 - generator.initial_step を呼び state/payload と session_data を返す
 - apply: 受け取った session_data を復元し generator.apply_step を呼ぶ
 - finalize: 復元 -> generator.finalize_step -> Excel/PDF/ZIP StreamingResponse
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

from app.api.services.report.base_interactive_report_generator import (
    BaseInteractiveReportGenerator,
)
from app.api.services.report.report_processing_service import ReportProcessingService

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
        session_data = generator.serialize_state(state)

        return {
            "status": "success",
            "step": 0,
            "message": "initial completed",
            "data": payload,
            "session_data": session_data,
        }

    # -------- Apply (中間) --------
    def apply(
        self,
        generator: BaseInteractiveReportGenerator,
        session_data: Dict[str, Any],
        user_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        try:
            state = generator.deserialize_state(session_data)
            state, payload = generator.apply_step(state, user_input)
            session_data_updated = generator.serialize_state(state)
            return {
                "status": "success",
                "step": payload.get("step", 1),
                "message": payload.get("message", "applied"),
                "data": payload,
                "session_data": session_data_updated,
            }
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
        session_data: Dict[str, Any],
    ) -> StreamingResponse | JSONResponse:
        try:
            state = generator.deserialize_state(session_data)
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
            response = self.create_response(generator, final_df, report_date)
            summary = payload.get("summary")
            if isinstance(summary, dict):
                for k, v in summary.items():
                    try:
                        response.headers[f"X-Summary-{k}"] = str(v)
                    except Exception:  # noqa: BLE001
                        pass
            return response
        except Exception as e:  # noqa: BLE001
            # finalize は StreamingResponse 指定のため簡易 JSON を返す
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "code": "FINALIZE_FAILED",
                    "detail": str(e),
                },
            )
