"""Generate Management Sheet UseCase."""

from datetime import date
from io import BytesIO
from typing import Any

from app.application.usecases.reports.report_generation_utils import (
    generate_excel_from_dataframe,
)
from app.core.domain.reports.management_sheet import ManagementSheet
from app.core.usecases.reports.base_report_usecase import BaseReportUseCase
from app.core.usecases.reports.management_sheet_processor import (
    process as management_sheet_process,
)


class GenerateManagementSheetUseCase(BaseReportUseCase):
    """経営管理表生成 UseCase."""

    @property
    def report_key(self) -> str:
        return "management_sheet"

    @property
    def report_name(self) -> str:
        return "経営管理表"

    def create_domain_model(self, df_formatted: dict[str, Any]) -> ManagementSheet:
        """ドメインモデル生成（Step 4）"""
        return ManagementSheet.from_dataframes(
            df_formatted.get("shipment"),
            df_formatted.get("yard"),
            df_formatted.get("receive"),
        )

    def execute_domain_logic(self, df_formatted: dict[str, Any]) -> Any:
        """ドメインロジック実行（Step 5）"""
        return management_sheet_process(df_formatted)

    def generate_excel(self, result_df: Any, report_date: date) -> BytesIO:
        """Excel生成（Step 6）"""
        return generate_excel_from_dataframe(
            result_df=result_df,
            report_key=self.report_key,
            report_date=report_date,
        )
