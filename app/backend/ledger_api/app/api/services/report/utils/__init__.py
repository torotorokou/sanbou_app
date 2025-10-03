"""
Report generation utilities.

レポート生成に必要な各種ユーティリティ機能を提供します。

モジュール構成:
- config/: 設定管理
- io/: 入出力操作
- excel/: Excel操作
- dataframe/: DataFrame操作
- formatters/: フォーマッティング
- logging/: ロギング
- paths/: パス管理
- domain/: ドメイン固有ロジック
"""

# Config
from app.api.services.report.utils.config import (
    clean_na_strings,
    get_template_config,
    get_unit_price_table_csv,
)

# IO
from app.api.services.report.utils.io import (
    load_all_filtered_dataframes,
    load_master_and_template,
    write_values_to_template,
)

# Excel
from app.api.services.report.utils.excel import (
    sort_by_cell_row,
)

# DataFrame
from app.api.services.report.utils.dataframe import (
    apply_summary_all_items,
    apply_column_addition_by_keys,
)

# Formatters
from app.api.services.report.utils.formatters import (
    get_weekday_japanese,
    to_reiwa_format,
    set_value_fast_safe,
    summary_apply,
    multiply_columns,
    round_value_column_generic,
)

# Logging
from app.api.services.report.utils.logging import app_logger

# Paths
from app.api.services.report.utils.paths import MainPath

# Domain
from app.api.services.report.utils.domain import ReadTransportDiscount

__all__ = [
    # Config
    "clean_na_strings",
    "get_template_config",
    "get_unit_price_table_csv",
    # IO
    "load_all_filtered_dataframes",
    "load_master_and_template",
    "write_values_to_template",
    # Excel
    "sort_by_cell_row",
    # DataFrame
    "apply_summary_all_items",
    "apply_column_addition_by_keys",
    # Formatters
    "get_weekday_japanese",
    "to_reiwa_format",
    "set_value_fast_safe",
    "summary_apply",
    "multiply_columns",
    "round_value_column_generic",
    # Logging
    "app_logger",
    # Paths
    "MainPath",
    # Domain
    "ReadTransportDiscount",
]
