# backend/app/api/services/report/core/concrete_generators.py
"""
旧版レポート生成クラス群

⚠️ 注意: これらのクラスは互換性維持のために保持されています。
新規開発では generate_*.py の UseCase クラスを使用してください。

推奨:
    - GenerateFactoryReportUseCase
    - GenerateBalanceSheetUseCase
    - GenerateAverageSheetUseCase
    - GenerateManagementSheetUseCase
"""

from typing import Any

import pandas as pd
from app.core.usecases.reports.average_sheet_processor import (
    process as process_average_sheet,
)
from app.core.usecases.reports.balance_sheet_processor import (
    process as process_balance_sheet,
)
from app.core.usecases.reports.base_generators import BaseReportGenerator
from app.core.usecases.reports.factory_report_processor import (
    process as process_factory_report,
)
from app.core.usecases.reports.management_sheet_processor import (
    process as process_management_sheet,
)


class FactoryReportGenerator(BaseReportGenerator):
    """工場レポート生成クラス（旧版）

    ⚠️ 互換性維持用。新規開発では GenerateFactoryReportUseCase を使用してください。
    """

    def main_process(self, df_formatted: dict[str, Any]) -> pd.DataFrame:
        return process_factory_report(df_formatted)


class BalanceSheetGenerator(BaseReportGenerator):
    """バランスシート生成クラス（旧版）

    ⚠️ 互換性維持用。新規開発では GenerateBalanceSheetUseCase を使用してください。
    """

    def main_process(self, df_formatted: dict[str, Any]) -> pd.DataFrame:
        return process_balance_sheet(df_formatted)


class AverageSheetGenerator(BaseReportGenerator):
    """平均シート生成クラス（旧版）

    ⚠️ 互換性維持用。新規開発では GenerateAverageSheetUseCase を使用してください。
    """

    def main_process(self, df_formatted: dict[str, Any]) -> pd.DataFrame:
        return process_average_sheet(df_formatted)


class ManagementSheetGenerator(BaseReportGenerator):
    """管理シート生成クラス（旧版）

    ⚠️ 互換性維持用。新規開発では GenerateManagementSheetUseCase を使用してください。
    """

    def main_process(self, df_formatted: dict[str, Any]) -> pd.DataFrame:
        return process_management_sheet(df_formatted)
