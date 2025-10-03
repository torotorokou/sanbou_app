"""
Core report service components.

レポート生成のコアコンポーネントを提供します。

モジュール構成:
- base_generators/: 基底ジェネレータークラス
- processors/: 処理サービス
- concrete_generators: 具体的なレポートジェネレーター実装
"""

from app.api.services.report.core.base_generators import (
    BaseReportGenerator,
    BaseInteractiveReportGenerator,
)
from app.api.services.report.core.processors import (
    ReportProcessingService,
    InteractiveReportProcessingService,
)

__all__ = [
    # Base generators
    "BaseReportGenerator",
    "BaseInteractiveReportGenerator",
    # Processors
    "ReportProcessingService",
    "InteractiveReportProcessingService",
]
