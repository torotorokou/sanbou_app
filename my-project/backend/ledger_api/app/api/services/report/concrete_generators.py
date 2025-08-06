# backend/app/api/services/concrete_generators.py

import pandas as pd
from .base_report_generator import BaseReportGenerator

from app.api.st_app.logic.manage.factory_report import process as process_factory_report
from app.api.st_app.logic.manage.balance_sheet import process as process_balance_sheet
from app.api.st_app.logic.manage.management_sheet import (
    process as process_management_sheet,
)
from app.api.st_app.logic.manage.average_sheet import process as process_average_sheet
from app.api.st_app.logic.manage.block_unit_price import (
    process as process_block_unit_price,
)


class FactoryReportGenerator(BaseReportGenerator):
    """工場レポート生成クラス"""

    def _main_process_impl(self) -> pd.DataFrame:
        result_df = process_factory_report(self.files)
        return result_df


class BalanceSheetGenerator(BaseReportGenerator):
    """バランスシート生成クラス"""

    def _main_process_impl(self) -> pd.DataFrame:
        result_df = process_balance_sheet(self.files)
        return result_df


class AverageSheetGenerator(BaseReportGenerator):
    """平均シート生成クラス"""

    def _main_process_impl(self) -> pd.DataFrame:
        result_df = process_average_sheet(self.files)
        return result_df


class BlockUnitPriceGenerator(BaseReportGenerator):
    """ブロック単価生成クラス"""

    def _main_process_impl(self) -> pd.DataFrame:
        result_df = process_block_unit_price(self.files)
        return result_df


class ManagementSheetGenerator(BaseReportGenerator):
    """管理シート生成クラス"""

    def _main_process_impl(self) -> pd.DataFrame:
        result_df = process_management_sheet(self.files)
        return result_df
