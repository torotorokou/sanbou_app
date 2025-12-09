"""
Generate Balance Sheet UseCase.

搬出入収支表生成のアプリケーションロジックを提供します。
factory_reportと同じClean Architectureパターンを適用。
"""

from datetime import date
from io import BytesIO
from typing import Any, Dict

from app.core.ports.inbound import CsvGateway, ReportRepository
from app.core.domain.reports.balance_sheet import BalanceSheet
from app.core.usecases.reports.base_report_usecase import BaseReportUseCase
from app.core.usecases.reports.balance_sheet import process as balance_sheet_process
from app.infra.report_utils.excel_writer import write_values_to_template
from app.infra.report_utils.template_config import get_template_config


class GenerateBalanceSheetUseCase(BaseReportUseCase):
    """搬出入収支表生成 UseCase."""
    
    @property
    def report_key(self) -> str:
        return "balance_sheet"
    
    @property
    def report_name(self) -> str:
        return "搬出入収支表"

    def create_domain_model(self, df_formatted: Dict[str, Any]) -> BalanceSheet:
        """ドメインモデル生成（Step 4）"""
        return BalanceSheet.from_dataframes(
            df_receive=df_formatted.get("receive"),
            df_shipment=df_formatted.get("shipment"),
            df_yard=df_formatted.get("yard"),
        )

    def execute_domain_logic(self, df_formatted: Dict[str, Any]) -> Any:
        """ドメインロジック実行（Step 5）"""
        return balance_sheet_process(df_formatted)

    def generate_excel(self, result_df: Any, report_date: date) -> BytesIO:
        """Excel生成（Step 6） - テンプレート使用"""
        template_config = get_template_config()["balance_sheet"]
        template_path = template_config["template_excel_path"]
        extracted_date = report_date.strftime("%Y年%m月%d日")
        
        return write_values_to_template(
            df=result_df,
            template_path=template_path,
            extracted_date=extracted_date,
        )


