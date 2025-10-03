"""
Formatting utilities for report generation.

日付、値の設定、サマリー、計算、丸め処理などのフォーマッティングを提供します。
"""

from app.api.services.report.utils.formatters.dates import (
    get_weekday_japanese,
    to_reiwa_format,
    to_japanese_era,
    to_japanese_month_day,
    get_title_from_date,
)
from app.api.services.report.utils.formatters.value_setter import (
    set_value_fast_safe,
)
from app.api.services.report.utils.formatters.summary import (
    summary_apply,
    summarize_value_by_cell_with_label,
    safe_merge_by_keys,
    summary_update_column_if_notna,
    write_sum_to_target_cell,
)
from app.api.services.report.utils.formatters.multiply import (
    multiply_columns,
)
from app.api.services.report.utils.formatters.rounding import (
    round_value_column_generic,
)

__all__ = [
    # Dates
    "get_weekday_japanese",
    "to_reiwa_format",
    "to_japanese_era",
    "to_japanese_month_day",
    "get_title_from_date",
    # Value setter
    "set_value_fast_safe",
    # Summary
    "summary_apply",
    "summarize_value_by_cell_with_label",
    "safe_merge_by_keys",
    "summary_update_column_if_notna",
    "write_sum_to_target_cell",
    # Multiply
    "multiply_columns",
    # Rounding
    "round_value_column_generic",
]
