"""Generate Block Unit Price UseCase."""

import time
from datetime import date
from io import BytesIO

from app.application.usecases.reports.report_generation_utils import (
    generate_excel_from_dataframe,
    generate_pdf_from_excel,
)
from app.core.domain.reports.block_unit_price import BlockUnitPrice
from app.core.ports.inbound import CsvGateway, ReportRepository
from app.core.usecases.reports.interactive.block_unit_price_initial import (
    execute_initial_step,
)
from backend_shared.application.logging import get_module_logger
from backend_shared.infra.adapters.fastapi.error_handlers import DomainError
from backend_shared.utils.date_filter_utils import (
    filter_by_period_from_max_date as shared_filter_by_period_from_max_date,
)
from fastapi import UploadFile
from fastapi.responses import JSONResponse

logger = get_module_logger(__name__)


class GenerateBlockUnitPriceUseCase:
    REPORT_KEY = "block_unit_price"

    def __init__(self, csv_gateway: CsvGateway, report_repository: ReportRepository):
        self.csv_gateway, self.report_repository = csv_gateway, report_repository

    def execute(
        self,
        shipment: UploadFile | None = None,
        yard: UploadFile | None = None,
        receive: UploadFile | None = None,
        period_type: str | None = None,
    ) -> JSONResponse:
        start_time = time.time()
        file_keys = [
            k
            for k, v in {"shipment": shipment, "yard": yard, "receive": receive}.items()
            if v
        ]

        logger.info(
            "ブロック単価表生成開始",
            extra={
                "usecase": "block_unit_price",
                "file_keys": file_keys,
                "period_type": period_type,
            },
        )

        try:
            # Step 1: CSV読み込み
            step_start = time.time()
            logger.debug("Step 1: CSV読み込み開始")

            files = {
                k: v
                for k, v in {
                    "shipment": shipment,
                    "yard": yard,
                    "receive": receive,
                }.items()
                if v
            }
            dfs, error = self.csv_gateway.read_csv_files(files)
            if error:
                logger.warning(
                    "Step 1: CSV読み込みエラー",
                    extra={"error_type": type(error).__name__},
                )
                return error.to_json_response()

            assert dfs is not None
            logger.debug(
                "Step 1: CSV読み込み完了",
                extra={"elapsed_seconds": round(time.time() - step_start, 3)},
            )

            # Step 2: 期間フィルタ（オプション）
            if period_type:
                step_start = time.time()
                logger.debug(
                    "Step 2: 期間フィルタ適用開始", extra={"period_type": period_type}
                )

                try:
                    dfs = shared_filter_by_period_from_max_date(dfs, period_type)
                    logger.debug(
                        "Step 2: 期間フィルタ適用完了",
                        extra={
                            "period_type": period_type,
                            "elapsed_seconds": round(time.time() - step_start, 3),
                        },
                    )
                except Exception as e:
                    logger.warning(
                        "Step 2: 期間フィルタスキップ（エラー）",
                        extra={"exception": str(e)},
                    )

            # Step 3: CSV整形
            step_start = time.time()
            logger.debug("Step 3: CSV整形開始")

            df_formatted = self.csv_gateway.format_csv_data(dfs)
            logger.debug(
                "Step 3: CSV整形完了",
                extra={"elapsed_seconds": round(time.time() - step_start, 3)},
            )

            # Step 4: ドメインモデル生成
            step_start = time.time()
            logger.debug("Step 4: ドメインモデル生成開始")

            block_unit_price = BlockUnitPrice.from_dataframes(
                df_formatted.get("shipment"),
                df_formatted.get("yard"),
                df_formatted.get("receive"),
            )
            logger.debug(
                "Step 4: ドメインモデル生成完了",
                extra={
                    "report_date": block_unit_price.report_date.isoformat(),
                    "elapsed_seconds": round(time.time() - step_start, 3),
                },
            )

            # Step 5: ドメインロジック実行（初期ステップのみ）
            step_start = time.time()
            logger.debug("Step 5: ドメインロジック実行開始（初期ステップ）")

            result_df, _ = execute_initial_step(df_formatted)
            logger.debug(
                "Step 5: ドメインロジック実行完了",
                extra={"elapsed_seconds": round(time.time() - step_start, 3)},
            )

            # Step 6: Excel生成
            step_start = time.time()
            logger.debug("Step 6: Excel生成開始")

            excel_bytes = self._generate_excel(result_df, block_unit_price.report_date)
            logger.debug(
                "Step 6: Excel生成完了",
                extra={
                    "size_bytes": len(excel_bytes.getvalue()),
                    "elapsed_seconds": round(time.time() - step_start, 3),
                },
            )

            # Step 7: PDF生成
            step_start = time.time()
            logger.debug("Step 7: PDF生成開始")

            pdf_bytes = self._generate_pdf(excel_bytes)
            logger.debug(
                "Step 7: PDF生成完了",
                extra={
                    "size_bytes": len(pdf_bytes.getvalue()),
                    "elapsed_seconds": round(time.time() - step_start, 3),
                },
            )

            # Step 8: 保存とURL生成
            step_start = time.time()
            logger.debug("Step 8: 保存とURL生成開始")

            artifact_urls = self.report_repository.save_report(
                "block_unit_price", block_unit_price.report_date, excel_bytes, pdf_bytes
            )
            logger.debug(
                "Step 8: 保存とURL生成完了",
                extra={"elapsed_seconds": round(time.time() - step_start, 3)},
            )

            # Step 9: レスポンス返却
            total_elapsed = time.time() - start_time
            logger.info(
                "ブロック単価表生成完了",
                extra={
                    "usecase": "block_unit_price",
                    "report_date": block_unit_price.report_date.isoformat(),
                    "total_elapsed_seconds": round(total_elapsed, 3),
                },
            )

            # BFF互換のレスポンス形式に変換
            artifact_dict = artifact_urls.to_dict()
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "ブロック単価表の生成が完了しました",
                    "report_key": "block_unit_price",
                    "report_date": block_unit_price.report_date.isoformat(),
                    "artifact": {
                        "excel_download_url": artifact_dict["excel_url"],
                        "pdf_preview_url": artifact_dict["pdf_url"],
                    },
                },
            )
        except DomainError:
            raise
        except Exception as ex:
            logger.exception(
                "ブロック単価表生成失敗",
                extra={
                    "usecase": "block_unit_price",
                    "error": str(ex),
                    "elapsed_seconds": round(time.time() - start_time, 3),
                },
                exc_info=True,
            )
            raise DomainError(
                "INTERNAL_ERROR",
                500,
                "ブロック単価表の生成中に予期しないエラーが発生しました",
                "内部エラー",
            ) from ex

    def _generate_excel(self, result_df, report_date: date) -> BytesIO:
        return generate_excel_from_dataframe(
            result_df=result_df,
            report_key=self.REPORT_KEY,
            report_date=report_date,
        )

    def _generate_pdf(self, excel_bytes: BytesIO) -> BytesIO:
        return generate_pdf_from_excel(excel_bytes)
