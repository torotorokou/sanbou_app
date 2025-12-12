"""
帳簿作成 UseCases パッケージ

Clean Architecture に基づく帳簿生成のユースケースを提供します。

エクスポート:
    UseCases（推奨）:
        - GenerateFactoryReportUseCase: 工場日報生成
        - GenerateBalanceSheetUseCase: 搬出入収支表生成
        - GenerateAverageSheetUseCase: 単価平均表生成
        - GenerateManagementSheetUseCase: 経営表生成
        - GenerateBlockUnitPriceUseCase: ブロック単価生成
    
    process関数（互換性維持用、新規開発では UseCase を使用してください）:
        - factory_report_process
        - balance_sheet_process
        - average_sheet_process
        - management_sheet_process
"""

# ==============================================================================
# UseCase Classes（推奨）
# ==============================================================================
from .generate_factory_report import GenerateFactoryReportUseCase  # noqa: F401
from .generate_balance_sheet import GenerateBalanceSheetUseCase  # noqa: F401
from .generate_average_sheet import GenerateAverageSheetUseCase  # noqa: F401
from .generate_management_sheet import GenerateManagementSheetUseCase  # noqa: F401
from .generate_block_unit_price import GenerateBlockUnitPriceUseCase  # noqa: F401

# ==============================================================================
# Process Functions（互換性維持用）
# ==============================================================================
from .average_sheet_processor import process as average_sheet_process  # noqa: F401
from .balance_sheet_processor import process as balance_sheet_process  # noqa: F401
from .factory_report_processor import process as factory_report_process  # noqa: F401
from .management_sheet_processor import process as management_sheet_process  # noqa: F401

# ==============================================================================
# __all__ 定義
# ==============================================================================
__all__ = [
    # UseCases
    "GenerateFactoryReportUseCase",
    "GenerateBalanceSheetUseCase",
    "GenerateAverageSheetUseCase",
    "GenerateManagementSheetUseCase",
    "GenerateBlockUnitPriceUseCase",
    # Process Functions (互換性維持)
    "factory_report_process",
    "balance_sheet_process",
    "average_sheet_process",
    "management_sheet_process",
]
