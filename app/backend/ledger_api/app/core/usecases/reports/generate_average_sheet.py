"""
Generate Average Sheet UseCase.

単価平均表生成のアプリケーションロジック。
"""
from datetime import date
from io import BytesIO
from typing import Any, Dict

from app.core.ports.inbound import CsvGateway, ReportRepository
from app.core.domain.reports.average_sheet import AverageSheet
from app.core.usecases.reports.base_report_usecase import BaseReportUseCase
from app.core.usecases.reports.average_sheet_processor import process as average_sheet_process
from app.application.usecases.reports.report_generation_utils import (
    generate_excel_from_dataframe,
)


class GenerateAverageSheetUseCase(BaseReportUseCase):
    """単価平均表生成 UseCase."""
    
    @property
    def report_key(self) -> str:
        return "average_sheet"
    
    @property
    def report_name(self) -> str:
        return "単価平均表"

    def create_domain_model(self, df_formatted: Dict[str, Any]) -> AverageSheet:
        """ドメインモデル生成（Step 4）"""
        return AverageSheet.from_dataframes(
            df_shipment=df_formatted.get("shipment"),
            df_yard=df_formatted.get("yard"),
            df_receive=df_formatted.get("receive"),
        )

    def execute_domain_logic(self, df_formatted: Dict[str, Any]) -> Any:
        """ドメインロジック実行（Step 5）"""
        return average_sheet_process(df_formatted)

    def generate_excel(self, result_df: Any, report_date: date) -> BytesIO:
        """Excel生成（Step 6）"""
        return generate_excel_from_dataframe(
            result_df=result_df,
            report_key=self.report_key,
            report_date=report_date,
        )

