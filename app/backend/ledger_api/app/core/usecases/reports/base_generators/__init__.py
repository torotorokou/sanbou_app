"""
Core base generators for report generation.

レポート生成の基底クラスを提供します。

モジュール:
- base_report_generator: 通常のレポート生成基底クラス
- base_interactive_report_generator: インタラクティブレポート生成基底クラス
"""

from app.core.usecases.reports.base_generators.base_interactive_report_generator import (
    BaseInteractiveReportGenerator,
)
from app.core.usecases.reports.base_generators.base_report_generator import (
    BaseReportGenerator,
)


__all__ = [
    "BaseReportGenerator",
    "BaseInteractiveReportGenerator",
]
