"""Generate Management Sheet UseCase."""
import time
from datetime import date
from io import BytesIO
from pathlib import Path
import tempfile
from typing import Optional
from fastapi import UploadFile
from fastapi.responses import JSONResponse
from app.core.ports.inbound import CsvGateway, ReportRepository
from app.core.domain.reports.management_sheet import ManagementSheet
from backend_shared.infra.adapters.fastapi.error_handlers import DomainError
from backend_shared.application.logging import get_module_logger, create_log_context
from backend_shared.utils.date_filter_utils import filter_by_period_from_max_date as shared_filter_by_period_from_max_date
from app.core.usecases.reports.management_sheet import process as management_sheet_process
from app.infra.report_utils import write_values_to_template, get_template_config
from app.infra.utils.pdf_conversion import convert_excel_to_pdf

logger = get_module_logger(__name__)


class GenerateManagementSheetUseCase:
    def __init__(self, csv_gateway: CsvGateway, report_repository: ReportRepository):
        self.csv_gateway, self.report_repository = csv_gateway, report_repository

    def execute(self, shipment: Optional[UploadFile] = None, yard: Optional[UploadFile] = None, receive: Optional[UploadFile] = None, period_type: Optional[str] = None) -> JSONResponse:
        start_time = time.time()
        file_keys = [k for k, v in {"shipment": shipment, "yard": yard, "receive": receive}.items() if v]
        
        logger.info(
            "経営管理表生成開始",
            extra={
                "usecase": "management_sheet",
                "file_keys": file_keys,
                "period_type": period_type,
            },
        )
        
        try:
            # Step 1: CSV読み込み
            step_start = time.time()
            logger.debug("Step 1: CSV読み込み開始")
            
            files = {k: v for k, v in {"shipment": shipment, "yard": yard, "receive": receive}.items() if v is not None}
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
                logger.debug("Step 2: 期間フィルタ適用開始", extra={"period_type": period_type})
                
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
            
            management_sheet = ManagementSheet.from_dataframes(df_formatted.get("shipment"), df_formatted.get("yard"), df_formatted.get("receive"))
            logger.debug(
                "Step 4: ドメインモデル生成完了",
                extra={
                    "report_date": management_sheet.report_date.isoformat(),
                    "elapsed_seconds": round(time.time() - step_start, 3),
                },
            )
            
            # Step 5: ドメインロジック実行
            step_start = time.time()
            logger.debug("Step 5: ドメインロジック実行開始")
            
            result_df = management_sheet_process(df_formatted)
            logger.debug(
                "Step 5: ドメインロジック実行完了",
                extra={"elapsed_seconds": round(time.time() - step_start, 3)},
            )
            
            # Step 6: Excel生成
            step_start = time.time()
            logger.debug("Step 6: Excel生成開始")
            
            excel_bytes = self._generate_excel(result_df, management_sheet.report_date)
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
            
            artifact_urls = self.report_repository.save_report("management_sheet", management_sheet.report_date, excel_bytes, pdf_bytes)
            logger.debug(
                "Step 8: 保存とURL生成完了",
                extra={"elapsed_seconds": round(time.time() - step_start, 3)},
            )
            
            # Step 9: レスポンス返却
            total_elapsed = time.time() - start_time
            logger.info(
                "経営管理表生成完了",
                extra={
                    "usecase": "management_sheet",
                    "report_date": management_sheet.report_date.isoformat(),
                    "total_elapsed_seconds": round(total_elapsed, 3),
                },
            )
            
            # BFF互換のレスポンス形式に変換
            artifact_dict = artifact_urls.to_dict()
            return JSONResponse(
                status_code=200,
                content={
                    "message": "経営管理表の生成が完了しました",
                    "report_date": management_sheet.report_date.isoformat(),
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
                "経営管理表生成失敗",
                extra={
                    "usecase": "management_sheet",
                    "error": str(ex),
                    "elapsed_seconds": round(time.time() - start_time, 3),
                },
                exc_info=True,
            )
            raise DomainError("INTERNAL_ERROR", 500, "経営管理表の生成中に予期しないエラーが発生しました", "内部エラー") from ex

    def _generate_excel(self, result_df, report_date: date) -> BytesIO:
        config = get_template_config()["management_sheet"]
        extracted_date = report_date.strftime("%Y年%m月%d日")
        buffer = write_values_to_template(result_df, config["template_excel_path"], extracted_date)
        return buffer

    def _generate_pdf(self, excel_bytes: BytesIO) -> BytesIO:
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp.write(excel_bytes.getvalue())
            tmp_path = Path(tmp.name)
        try:
            pdf_bytes_raw = convert_excel_to_pdf(tmp_path)
            return BytesIO(pdf_bytes_raw)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()
