"""Generate Management Sheet UseCase."""
from datetime import date
from io import BytesIO
from pathlib import Path
import tempfile
from typing import Optional
from fastapi import UploadFile
from fastapi.responses import JSONResponse
from app.core.ports import CsvGateway, ReportRepository
from app.core.domain.reports.management_sheet import ManagementSheet
from backend_shared.adapters.fastapi.error_handlers import DomainError
from backend_shared.utils.date_filter_utils import filter_by_period_from_min_date as shared_filter_by_period_from_min_date
from app.api.services.report.ledger.management_sheet import process as management_sheet_process
from app.api.services.report.utils.io import write_values_to_template
from app.api.services.report.utils.config import get_template_config
from app.api.utils.pdf_conversion import convert_excel_to_pdf


class GenerateManagementSheetUseCase:
    def __init__(self, csv_gateway: CsvGateway, report_repository: ReportRepository):
        self.csv_gateway, self.report_repository = csv_gateway, report_repository

    async def execute(self, shipment: Optional[UploadFile] = None, yard: Optional[UploadFile] = None, receive: Optional[UploadFile] = None, period_type: Optional[str] = None) -> JSONResponse:
        try:
            files = {k: v for k, v in {"shipment": shipment, "yard": yard, "receive": receive}.items() if v}
            dfs = await self.csv_gateway.read_csv_files(files)
            if period_type:
                try:
                    dfs = shared_filter_by_period_from_min_date(dfs, period_type)
                except:
                    pass
            df_formatted = self.csv_gateway.format_csv_data(dfs)
            management_sheet = ManagementSheet.from_dataframes(df_formatted.get("shipment"), df_formatted.get("yard"), df_formatted.get("receive"))
            result_df = management_sheet_process(df_formatted)
            excel_bytes = self._generate_excel(result_df, management_sheet.report_date)
            pdf_bytes = self._generate_pdf(excel_bytes)
            artifact_urls = self.report_repository.save_report("management_sheet", management_sheet.report_date, excel_bytes, pdf_bytes)
            return JSONResponse(status_code=200, content={"message": "経営管理表の生成が完了しました", "report_date": management_sheet.report_date.isoformat(), **artifact_urls.to_dict()})
        except DomainError:
            raise
        except Exception as ex:
            raise DomainError("INTERNAL_ERROR", 500, "経営管理表の生成中に予期しないエラーが発生しました", "内部エラー") from ex

    def _generate_excel(self, result_df, report_date: date) -> bytes:
        config = get_template_config()["management_sheet"]
        buffer = write_values_to_template(result_df, config["template_path"], report_date.isoformat())
        buffer.seek(0)
        return buffer.read()

    def _generate_pdf(self, excel_bytes: bytes) -> bytes:
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp.write(excel_bytes)
            tmp_path = Path(tmp.name)
        try:
            return convert_excel_to_pdf(tmp_path)
        finally:
            tmp_path.unlink(missing_ok=True)
