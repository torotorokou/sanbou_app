# backend/app/api/services/report/concrete_generators.py

from typing import Any, Dict

import pandas as pd

from app.api.st_app.logic.manage.average_sheet import process as process_average_sheet
from app.api.st_app.logic.manage.balance_sheet import process as process_balance_sheet
from app.api.st_app.logic.manage.factory_report import process as process_factory_report
from app.api.st_app.logic.manage.management_sheet import (
    process as process_management_sheet,
)

from .base_report_generator import BaseReportGenerator
from .generator_factory import register


@register("factory_report")
class FactoryReportGenerator(BaseReportGenerator):
    """工場レポート生成クラス"""

    def main_process(self, df_formatted: Dict[str, Any]) -> pd.DataFrame:
        return process_factory_report(df_formatted)


@register("balance_sheet")
class BalanceSheetGenerator(BaseReportGenerator):
    """バランスシート生成クラス"""

    def main_process(self, df_formatted: Dict[str, Any]) -> pd.DataFrame:
        return process_balance_sheet(df_formatted)


@register("average_sheet")
class AverageSheetGenerator(BaseReportGenerator):
    """平均シート生成クラス"""

    def main_process(self, df_formatted: Dict[str, Any]) -> pd.DataFrame:
        return process_average_sheet(df_formatted)


@register("block_unit_price")
class BlockUnitPriceGenerator(BaseReportGenerator):
    """ブロック単価生成クラス（対話型のみ）"""

    def __init__(
        self, report_key: str, files: Dict[str, Any], interactive: bool = True
    ):
        super().__init__(report_key, files)
        self.interactive = interactive

    def main_process(self, df_formatted: Dict[str, Any]) -> pd.DataFrame:
        # 対話型処理のみを実行
        from app.api.st_app.logic.manage.block_unit_price_react import (
            process as process_block_unit_price,
        )

        return process_block_unit_price(df_formatted)


@register("management_sheet")
class ManagementSheetGenerator(BaseReportGenerator):
    """管理シート生成クラス"""

    def main_process(self, df_formatted: Dict[str, Any]) -> pd.DataFrame:
        return process_management_sheet(df_formatted)
