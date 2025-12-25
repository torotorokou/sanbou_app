"""帳票処理の共通サービス:
- CSV 読込
- ジェネレーターの validate/format/main_process 呼び出し
- Excel/PDF をファイルとして保存し、署名付き URL を返却

🔄 リファクタリング: Excel同期 + PDF非同期の2段階構成に対応
"""

import traceback
from typing import Any

from backend_shared.application.logging import get_module_logger

# pandas はこのモジュールでは未使用
from fastapi import BackgroundTasks, UploadFile
from fastapi.responses import JSONResponse, Response

logger = get_module_logger(__name__)

from app.core.usecases.reports.base_generators import BaseReportGenerator
from backend_shared.infra.adapters.fastapi.error_handlers import DomainError
from backend_shared.infra.adapters.presentation.response_error import (
    NoFilesUploadedResponse,
)
from backend_shared.utils.csv_reader import read_csv_files
from backend_shared.utils.date_filter_utils import (
    filter_by_period_from_max_date as shared_filter_by_period_from_max_date,
)


def _ensure_bytes(value: Any, *, label: str) -> bytes:
    """Ensure the provided value is bytes.

    👶 Pydantic や BytesIO など様々な型が返る可能性があるため、ここで統一しておきます。
    """

    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    try:
        # BytesIO やファイルライクオブジェクトをサポート
        if hasattr(value, "getvalue"):
            return bytes(value.getvalue())  # type: ignore[call-overload]
        if hasattr(value, "read"):
            data = value.read()
            return bytes(data)
    except Exception as exc:  # noqa: BLE001
        raise TypeError(f"{label}: could not normalise to bytes") from exc
    raise TypeError(f"{label}: unsupported type {type(value)!r}")


class ReportProcessingService:
    """帳票処理の共通サービスクラス"""

    def __init__(self):
        pass

    def _read_uploaded_files(
        self, files: dict[str, UploadFile]
    ) -> tuple[dict[str, Any] | None, Any | None]:
        """CSV読込のみを担当。空チェックも含む。"""
        if not files:
            logger.warning("No files uploaded")
            return None, NoFilesUploadedResponse()

        logger.debug(
            "Processing uploaded files", extra={"file_keys": list(files.keys())}
        )

        dfs, error = read_csv_files(files)
        if error:
            return None, error
        return dfs, None

    def run(
        self,
        generator: BaseReportGenerator,
        files: dict[str, UploadFile],
        background_tasks: BackgroundTasks | None = None,
        async_pdf: bool = True,
    ) -> Response:
        """
        完全な帳票処理フローを実行（Factory不要・各エンドポイントがGeneratorを生成）

        Args:
            generator: レポートジェネレーター
            files: アップロードされたCSVファイル
            background_tasks: FastAPIのBackgroundTasks（PDF非同期生成用）
            async_pdf: True=PDF非同期生成, False=同期生成（従来互換）
        """
        try:
            # Step 1: CSV読込
            dfs, error = self._read_uploaded_files(files)
            if error:
                return error.to_json_response()

            assert dfs is not None

            # Step 2: 検証（ジェネレーター定義）
            validation_error = generator.validate(dfs, files)
            if validation_error:
                logger.warning(
                    "Validation failed", extra={"error": str(validation_error)}
                )
                return validation_error.to_json_response()

            # Step 2.5: 帳簿ごとの期間指定があれば、最小伝票日付から日/週/月でフィルタ
            period_type = getattr(generator, "period_type", None)
            if period_type:
                logger.debug(
                    "Starting CSV date filtering", extra={"period_type": period_type}
                )
                logger.debug("DataFrame shapes BEFORE filtering")
                for csv_type, df in dfs.items():
                    try:
                        shape = getattr(df, "shape", None)
                        columns = list(df.columns)
                        candidates = ["伝票日付", "日付", "date", "Date"]
                        found = [c for c in candidates if c in df.columns]
                        samples = {col: df[col].head(3).tolist() for col in found}
                        logger.debug(
                            "DataFrame info before filtering",
                            extra={
                                "csv_type": csv_type,
                                "shape": shape,
                                "columns": columns,
                                "date_columns_found": found,
                                "sample_values": samples,
                            },
                        )
                    except Exception as ex:
                        logger.debug(
                            "DataFrame info unavailable",
                            extra={"csv_type": csv_type, "error": str(ex)},
                        )

                try:
                    dfs = shared_filter_by_period_from_max_date(dfs, period_type)
                    logger.info(
                        "Applied date filtering", extra={"period_type": period_type}
                    )
                    logger.debug("DataFrame shapes AFTER filtering")
                    for csv_type, df in dfs.items():
                        try:
                            shape = getattr(df, "shape", None)
                            logger.debug(
                                "DataFrame shape after filtering",
                                extra={"csv_type": csv_type, "shape": shape},
                            )
                        except Exception:
                            logger.debug(
                                "DataFrame shape unavailable after filtering",
                                extra={"csv_type": csv_type},
                            )
                except Exception as e:
                    logger.warning(
                        "Date filtering skipped due to error",
                        extra={"error": str(e)},
                        exc_info=True,
                    )
                logger.debug("Completed CSV date filtering")

            # Step 3: 整形（ジェネレーター定義）
            logger.debug("Formatting DataFrames")
            try:
                df_formatted = generator.format(dfs)
            except DomainError:
                # 既にDomainErrorの場合はそのまま再raise
                raise
            except Exception as ex:
                logger.error("format() failed", extra={"error": str(ex)}, exc_info=True)
                raise DomainError(
                    code="REPORT_FORMAT_ERROR",
                    status=500,
                    user_message=f"帳票データの整形中にエラーが発生しました: {str(ex)}",
                    title="データ整形エラー",
                ) from ex

            for csv_type, df in df_formatted.items():
                try:
                    shape = getattr(df, "shape", None)
                    logger.debug(
                        "Formatted DataFrame",
                        extra={"csv_type": csv_type, "shape": shape},
                    )
                except Exception:
                    pass

            # Step 4: メイン処理（ジェネレーター定義）
            logger.debug("Running main_process")
            try:
                df_result = generator.main_process(df_formatted)
            except DomainError:
                # 既にDomainErrorの場合はそのまま再raise
                raise
            except Exception as ex:
                logger.error(
                    "main_process raised an exception",
                    extra={
                        "exception_type": type(ex).__name__,
                        "message": str(ex),
                        "traceback": traceback.format_exc(),
                    },
                    exc_info=True,
                )
                # DomainErrorに変換して詳細なエラーメッセージを提供
                raise DomainError(
                    code="REPORT_PROCESSING_ERROR",
                    status=500,
                    user_message=f"帳票の計算処理中にエラーが発生しました: {str(ex)}",
                    title="帳票処理エラー",
                ) from ex

            # Step 5: 帳票日付作成（共通: 整形後データから）
            logger.debug("Making report date")
            report_date = generator.make_report_date(df_formatted)

            # Step 6: Excel/PDF を保存し JSON で URL を返す
            return self.create_response(
                generator,
                df_result,
                report_date,
                background_tasks=background_tasks,
                async_pdf=async_pdf,
            )

        except DomainError:
            # DomainErrorはそのまま再raiseしてFastAPIのエラーハンドラに任せる
            raise
        except Exception as e:  # 予期せぬ例外をDomainErrorに変換
            logger.error(
                "Report processing failed",
                extra={"error": str(e), "traceback": traceback.format_exc()},
                exc_info=True,
            )

            # DomainErrorとして再raiseし、エラーハンドラでProblemDetails化
            raise DomainError(
                code="REPORT_GENERATION_ERROR",
                status=500,
                user_message=f"帳票の生成中にエラーが発生しました: {str(e)}",
                title="帳票生成エラー",
            ) from e

    # ---------- 日付フィルタ関連（共通ユーティリティ） ----------
    # 共通化: 旧ローカル実装は date_filter_utils に移動
    # def filter_by_period_from_min_date(...): pass
    # def _find_date_column(...): pass

    def create_response(
        self,
        generator: BaseReportGenerator,
        df_result: Any,
        report_date: str,
        *,
        extra_payload: dict[str, Any] | None = None,
        background_tasks: BackgroundTasks | None = None,
        async_pdf: bool = True,
    ) -> JSONResponse:
        """Excel/PDF を保存し、署名付き URL を含む JSON を返却する。

        Args:
            generator: レポートジェネレーター
            df_result: 処理結果DataFrame
            report_date: レポート日付
            extra_payload: 追加のペイロード
            background_tasks: FastAPIのBackgroundTasks（PDF非同期生成用）
            async_pdf: True=PDF非同期生成, False=同期生成
        """
        from app.infra.adapters.artifact_storage import ArtifactResponseBuilder
        from app.infra.adapters.artifact_storage.artifact_builder import (
            generate_pdf_background,
        )

        builder = ArtifactResponseBuilder()
        response = builder.build(
            generator,
            df_result,
            report_date,
            extra_payload=extra_payload,
            async_pdf=async_pdf,
        )

        # PDF非同期生成の場合、BackgroundTasksにタスクを登録
        if async_pdf and background_tasks is not None:
            # レスポンスからメタデータを取得
            import json

            response_body = json.loads(response.body.decode())
            metadata = response_body.get("metadata", {})
            excel_path = metadata.get("excel_path")
            artifact = response_body.get("artifact", {})
            report_token = artifact.get("report_token")
            report_key = response_body.get("report_key")

            if excel_path and report_token:
                background_tasks.add_task(
                    generate_pdf_background,
                    report_key=report_key,
                    report_date=report_date,
                    report_token=report_token,
                    excel_path_str=excel_path,
                )
                logger.info(
                    "PDF生成タスクをバックグラウンドに登録",
                    extra={
                        "report_key": report_key,
                        "report_date": report_date,
                        "report_token": report_token,
                    },
                )

        return response

    # 旧APIは撤廃（Factory廃止に伴い使用不可）
