# backend/app/api/services/report/core/concrete_generators.py

from typing import Any, Dict

import pandas as pd

from app.application.usecases.reports.average_sheet import process as process_average_sheet
from app.application.usecases.reports.balance_sheet import process as process_balance_sheet
from app.application.usecases.reports.factory_report import process as process_factory_report
from app.application.usecases.reports.management_sheet import (
    process as process_management_sheet,
)

from app.application.usecases.report.base_generators import BaseReportGenerator


class FactoryReportGenerator(BaseReportGenerator):
    """工場レポート生成クラス"""

    def main_process(self, df_formatted: Dict[str, Any]) -> pd.DataFrame:
        return process_factory_report(df_formatted)


class BalanceSheetGenerator(BaseReportGenerator):
    """バランスシート生成クラス"""

    def main_process(self, df_formatted: Dict[str, Any]) -> pd.DataFrame:
        return process_balance_sheet(df_formatted)


class AverageSheetGenerator(BaseReportGenerator):
    """平均シート生成クラス"""

    def main_process(self, df_formatted: Dict[str, Any]) -> pd.DataFrame:
        return process_average_sheet(df_formatted)


class BlockUnitPriceGenerator(BaseReportGenerator):
    """ブロック単価生成クラス（対話型のみ）"""

    def __init__(
        self, report_key: str, files: Dict[str, Any], interactive: bool = True
    ):
        super().__init__(report_key, files)
        self.interactive = interactive

    def main_process(self, df_formatted: Dict[str, Any]) -> pd.DataFrame:
        # 対話型処理のみを実行
        # 対話型は専用の Interactive クラスを使用
        from app.application.usecases.reports.interactive import (
            BlockUnitPriceInteractive,
        )
        from app.application.usecases.report.processors import (
            InteractiveReportProcessingService,
        )

        service = InteractiveReportProcessingService()
        generator = BlockUnitPriceInteractive(files=df_formatted)
        # 対話型の初期ステップを実行して、選択肢ペイロードを返す（レガシー互換）
        result = service.initial(generator, df_formatted)
        return result  # type: ignore[return-value]


class ManagementSheetGenerator(BaseReportGenerator):
    """管理シート生成クラス"""

    def main_process(self, df_formatted: Dict[str, Any]) -> pd.DataFrame:
        return process_management_sheet(df_formatted)
