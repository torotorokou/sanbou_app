"""Generate Block Unit Price UseCase."""
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
from app.core.domain.reports.block_unit_price import BlockUnitPrice
from backend_shared.adapters.fastapi.error_handlers import DomainError
from backend_shared.utils.date_filter_utils import filter_by_period_from_min_date as shared_filter_by_period_from_min_date
from app.api.services.report.ledger.interactive.block_unit_price_initial import execute_initial_step
from app.api.services.report.utils.io import write_values_to_template
from app.api.services.report.utils.config import get_template_config
from app.api.utils.pdf_conversion import convert_excel_to_pdf

logger = logging.getLogger(__name__)


class GenerateBlockUnitPriceUseCase:
    def __init__(self, csv_gateway: CsvGateway, report_repository: ReportRepository):
        self.csv_gateway, self.report_repository = csv_gateway, report_repository

    def execute(self, shipment: Optional[UploadFile] = None, yard: Optional[UploadFile] = None, receive: Optional[UploadFile] = None, period_type: Optional[str] = None) -> JSONResponse:
        try:
            files = {k: v for k, v in {"shipment": shipment, "yard": yard, "receive": receive}.items() if v}
            dfs = self.csv_gateway.read_csv_files(files)
            if period_type:
                try:
                    dfs = shared_filter_by_period_from_min_date(dfs, period_type)
                except:
                    pass
            df_formatted = self.csv_gateway.format_csv_data(dfs)
            block_unit_price = BlockUnitPrice.from_dataframes(df_formatted.get("shipment"), df_formatted.get("yard"), df_formatted.get("receive"))
            # block_unit_priceは初期ステップのみ実行（インタラクティブ機能は別途）
            result_df, _ = execute_initial_step(df_formatted)
            excel_bytes = self._generate_excel(result_df, block_unit_price.report_date)
            pdf_bytes = self._generate_pdf(excel_bytes)
            artifact_urls = self.report_repository.save_report("block_unit_price", block_unit_price.report_date, excel_bytes, pdf_bytes)
            return JSONResponse(status_code=200, content={"message": "ブロック単価表の生成が完了しました", "report_date": block_unit_price.report_date.isoformat(), **artifact_urls.to_dict()})
        except DomainError:
            raise
        except Exception as ex:
            raise DomainError("INTERNAL_ERROR", 500, "ブロック単価表の生成中に予期しないエラーが発生しました", "内部エラー") from ex

    def _generate_excel(self, result_df, report_date: date) -> BytesIO:
        config = get_template_config()["block_unit_price"]
        extracted_date = report_date.strftime("%Y年%m月%d日")
        buffer = write_values_to_template(result_df, config["template_path"], extracted_date)
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
