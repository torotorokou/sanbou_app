"""Value Objects - ドメイン層の値オブジェクト

値オブジェクトは不変性を持ち、ビジネスルールをカプセル化します。

Examples:
    >>> from app.core.domain.value_objects import DateRange, Money
    >>> from datetime import date
    >>> from decimal import Decimal
    >>> 
    >>> # 日付範囲の使用例
    >>> range1 = DateRange(date(2025, 1, 1), date(2025, 1, 31))
    >>> range1.days()
    31
    >>> 
    >>> # 金額の使用例
    >>> price = Money(Decimal("1000"), "JPY")
    >>> discounted = price * Decimal("0.9")
    >>> discounted.format()
    '¥900'
"""

from app.core.domain.value_objects.date_range import DateRange
from app.core.domain.value_objects.money import Money

__all__ = ["DateRange", "Money"]
