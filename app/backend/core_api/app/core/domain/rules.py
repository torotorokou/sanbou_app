"""
Domain rules and utilities (business logic).
TODO: Add営業日計算、祝日判定などのロジック.
"""

from datetime import date as date_type


def is_business_day(d: date_type) -> bool:
    """
    Check if the given date is a business day.
    TODO: Implement proper holiday calendar logic.
    """
    # Placeholder: weekdays only (Monday=0, Sunday=6)
    return d.weekday() < 5
