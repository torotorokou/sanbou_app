"""
Report service components.

レポート生成サービス全体を統括するパッケージです。

モジュール構成:
- core/: コアコンポーネント（基底クラス、処理サービス、具体的実装）
  - base_generators/: 基底ジェネレータークラス
  - processors/: 処理サービス
  - concrete_generators: 具体的なレポートジェネレーター
- artifacts/: アーティファクト管理（保存、署名URL）
- session/: セッション管理（インタラクティブレポート用）
- ledger/: 帳簿レポート実装
"""

# Core components
from app.application.usecases.report import (
    BaseReportGenerator,
    BaseInteractiveReportGenerator,
    ReportProcessingService,
    InteractiveReportProcessingService,
)

# Concrete generators
from app.application.usecases.report import (
    FactoryReportGenerator,
    BalanceSheetGenerator,
    AverageSheetGenerator,
    BlockUnitPriceGenerator,
    ManagementSheetGenerator,
)

# Artifacts
from app.infra.adapters.artifact_storage import (
    get_report_artifact_storage,
    ReportArtifactStorage,
    ArtifactResponseBuilder,
)

# Session
from app.infra.adapters.session import (
    session_store,
    SessionStore,
)

# 後方互換性のための再エクスポート
from app.api.services.report.core.base_generators.base_report_generator import (
    BaseReportGenerator as base_report_generator_compat,
)
from app.api.services.report.core.base_generators.base_interactive_report_generator import (
    BaseInteractiveReportGenerator as base_interactive_report_generator_compat,
)
from app.api.services.report.core.processors.report_processing_service import (
    ReportProcessingService as report_processing_service_compat,
)
from app.api.services.report.core.processors.interactive_report_processing_service import (
    InteractiveReportProcessingService as interactive_report_processing_service_compat,
)
from app.infra.adapters.artifact_storage import (
    get_report_artifact_storage as artifact_service_compat,
)
from app.infra.adapters.artifact_storage import (
    ArtifactResponseBuilder as artifact_builder_compat,
)
from app.infra.adapters.session import (
    session_store as session_store_compat,
)

# 後方互換性マッピング（モジュール名として解決できるように）
base_report_generator = base_report_generator_compat
base_interactive_report_generator = base_interactive_report_generator_compat
report_processing_service = report_processing_service_compat
interactive_report_processing_service = interactive_report_processing_service_compat
artifact_service = artifact_service_compat
artifact_builder = artifact_builder_compat
session_store_module = session_store_compat

__all__ = [
    # Core - Base generators
    "BaseReportGenerator",
    "BaseInteractiveReportGenerator",
    # Core - Processors
    "ReportProcessingService",
    "InteractiveReportProcessingService",
    # Core - Concrete generators
    "FactoryReportGenerator",
    "BalanceSheetGenerator",
    "AverageSheetGenerator",
    "BlockUnitPriceGenerator",
    "ManagementSheetGenerator",
    # Artifacts
    "get_report_artifact_storage",
    "ReportArtifactStorage",
    "ArtifactResponseBuilder",
    # Session
    "session_store",
    "SessionStore",
]
