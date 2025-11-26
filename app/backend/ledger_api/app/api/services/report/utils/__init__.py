"""
Report generation utilities (DEPRECATED - Use app.infra.report_utils).

このモジュールは後方互換性のためのみ残されています。
新しいコードでは app.infra.report_utils を使用してください。
"""

# Import from new location for backward compatibility
from app.infra.report_utils import (
    write_values_to_template,
    get_template_config,
    app_logger,
    MainPath,
    load_master_and_template,
    load_all_filtered_dataframes,
    clean_na_strings,
    formatters,
    dataframe,
    excel,
    ReadTransportDiscount,
)

# Config (still in old location)
from app.api.services.report.utils.config import (
    get_unit_price_table_csv,
)

# Re-export commonly used functions from sub-modules
from app.infra.report_utils.excel import sort_by_cell_row
from app.infra.report_utils.dataframe import (
    apply_summary_all_items,
    apply_column_addition_by_keys,
)
from app.infra.report_utils.formatters import (
    get_weekday_japanese,
    to_reiwa_format,
    set_value_fast_safe,
    summary_apply,
    multiply_columns,
    round_value_column_generic,
)

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
