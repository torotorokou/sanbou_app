"""
Generate Average Sheet UseCase.

単価平均表生成のアプリケーションロジック。
"""
import logging
import time
from datetime import date
from io import BytesIO
from pathlib import Path
import tempfile
from typing import Optional

from fastapi import UploadFile
from fastapi.responses import JSONResponse

from app.core.ports import CsvGateway, ReportRepository
from app.core.domain.reports.average_sheet import AverageSheet
from backend_shared.adapters.fastapi.error_handlers import DomainError
from backend_shared.utils.date_filter_utils import filter_by_period_from_min_date as shared_filter_by_period_from_min_date

from app.api.services.report.ledger.average_sheet import process as average_sheet_process
from app.api.services.report.utils.io import write_values_to_template
from app.api.services.report.utils.config import get_template_config
from app.api.utils.pdf_conversion import convert_excel_to_pdf

logger = logging.getLogger(__name__)


class GenerateAverageSheetUseCase:
    """単価平均表生成 UseCase."""

    def __init__(self, csv_gateway: CsvGateway, report_repository: ReportRepository):
        self.csv_gateway = csv_gateway
        self.report_repository = report_repository

    def execute(
        self,
        shipment: Optional[UploadFile] = None,
        yard: Optional[UploadFile] = None,
        receive: Optional[UploadFile] = None,
        period_type: Optional[str] = None,
    ) -> JSONResponse:
        start_time = time.time()
        file_keys = [k for k, v in {"shipment": shipment, "yard": yard, "receive": receive}.items() if v is not None]
        
        logger.info(
            "単価平均表生成開始",
            extra={
                "usecase": "average_sheet",
                "file_keys": file_keys,
                "period_type": period_type,
            },
        )
        
        try:
            # Step 1: CSV読み込み
            step_start = time.time()
            logger.debug("Step 1: CSV読み込み開始")
            
            files = {k: v for k, v in {"shipment": shipment, "yard": yard, "receive": receive}.items() if v is not None}
            dfs = self.csv_gateway.read_csv_files(files)
            
            logger.debug(
                "Step 1: CSV読み込み完了",
                extra={"elapsed_seconds": round(time.time() - step_start, 3)},
            )

            # Step 2: 期間フィルタ（オプション）
            if period_type:
                step_start = time.time()
                logger.debug("Step 2: 期間フィルタ適用開始", extra={"period_type": period_type})
                
                try:
                    dfs = shared_filter_by_period_from_min_date(dfs, period_type)
                    logger.debug(
                        "Step 2: 期間フィルタ適用完了",
                        extra={
                            "period_type": period_type,
                            "elapsed_seconds": round(time.time() - step_start, 3),
                        },
                    )
                except Exception as e:
                    logger.warning("Step 2: 期間フィルタスキップ（エラー）", extra={"exception": str(e)})

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
            
            average_sheet = AverageSheet.from_dataframes(
                df_shipment=df_formatted.get("shipment"),
                df_yard=df_formatted.get("yard"),
                df_receive=df_formatted.get("receive"),
            )
            
            logger.debug(
                "Step 4: ドメインモデル生成完了",
                extra={
                    "shipment_count": len(average_sheet.shipment_items),
                    "yard_count": len(average_sheet.yard_items),
                    "receive_count": len(average_sheet.receive_items),
                    "report_date": average_sheet.report_date.isoformat(),
                    "elapsed_seconds": round(time.time() - step_start, 3),
                },
            )

            # Step 5: ドメインロジック実行
            step_start = time.time()
            logger.debug("Step 5: ドメインロジック実行開始")
            
            result_df = average_sheet_process(df_formatted)
            logger.debug(
                "Step 5: ドメインロジック実行完了",
                extra={"elapsed_seconds": round(time.time() - step_start, 3)},
            )

            # Step 6: Excel生成
            step_start = time.time()
            logger.debug("Step 6: Excel生成開始")
            
            excel_bytes = self._generate_excel(result_df, average_sheet.report_date)
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
                report_key="average_sheet",
                report_date=average_sheet.report_date,
                excel_bytes=excel_bytes,
                pdf_bytes=pdf_bytes,
            )
            logger.debug(
                "Step 8: 保存とURL生成完了",
                extra={"elapsed_seconds": round(time.time() - step_start, 3)},
            )

            # Step 9: レスポンス返却
            total_elapsed = time.time() - start_time
            logger.info(
                "単価平均表生成完了",
                extra={
                    "usecase": "average_sheet",
                    "report_date": average_sheet.report_date.isoformat(),
                    "total_elapsed_seconds": round(total_elapsed, 3),
                },
            )
            
            return JSONResponse(
                status_code=200,
                content={
                    "message": "単価平均表の生成が完了しました",
                    "report_date": average_sheet.report_date.isoformat(),
                    **artifact_urls.to_dict(),
                },
            )
        except DomainError:
            raise
        except Exception as ex:
            logger.exception(
                "単価平均表生成失敗",
                extra={
                    "usecase": "average_sheet",
                    "error": str(ex),
                    "elapsed_seconds": round(time.time() - start_time, 3),
                },
                exc_info=True,
            )
            raise DomainError(
                code="INTERNAL_ERROR",
                status=500,
                user_message="単価平均表の生成中に予期しないエラーが発生しました",
                title="内部エラー",
            ) from ex

    def _generate_excel(self, result_df, report_date: date) -> BytesIO:
        template_config = get_template_config()["average_sheet"]
        template_path = template_config["template_path"]
        extracted_date = report_date.strftime("%Y年%m月%d日")
        
        excel_bytes = write_values_to_template(
            df=result_df,
            template_path=template_path,
            extracted_date=extracted_date,
        )
        return excel_bytes

    def _generate_pdf(self, excel_bytes: BytesIO) -> BytesIO:
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp.write(excel_bytes.getvalue())
            tmp_path = Path(tmp.name)
        try:
            pdf_bytes_raw = convert_excel_to_pdf(tmp_path)
            pdf_bytes = BytesIO(pdf_bytes_raw)
            return pdf_bytes
        finally:
            if tmp_path.exists():
                tmp_path.unlink()
