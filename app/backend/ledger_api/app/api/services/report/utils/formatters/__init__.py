"""
Formatting utilities for report generation (DEPRECATED - Use app.infra.report_utils.formatters).
"""

from app.infra.report_utils.formatters import (
    get_weekday_japanese,
    to_reiwa_format,
    to_japanese_era,
    to_japanese_month_day,
    get_title_from_date,
    set_value_fast_safe,
    summary_apply,
    summarize_value_by_cell_with_label,
    safe_merge_by_keys,
    summary_update_column_if_notna,
    write_sum_to_target_cell,
    multiply_columns,
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
