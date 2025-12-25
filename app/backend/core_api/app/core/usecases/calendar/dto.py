"""
Calendar UseCase DTOs

Input/Output DTOs for Calendar feature following Clean Architecture principles.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GetCalendarMonthInput:
    """
    Input DTO for getting calendar month data

    Attributes:
        year: 年 (1900-2100)
        month: 月 (1-12)
    """

    year: int
    month: int

    def validate(self) -> None:
        """
        入力値のバリデーション

        Raises:
            ValueError: 年月の範囲外
        """
        if not (1900 <= self.year <= 2100):
            raise ValueError(f"Invalid year: {self.year} (must be 1900-2100)")
        if not (1 <= self.month <= 12):
            raise ValueError(f"Invalid month: {self.month} (must be 1-12)")


@dataclass(frozen=True)
class GetCalendarMonthOutput:
    """
    Output DTO for calendar month data

    Attributes:
        calendar_days: カレンダーデータリスト（日ごとの営業日情報等）
    """

    calendar_days: list[dict[str, Any]]
