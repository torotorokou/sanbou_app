"""
Money Value Object - 金額を表す値オブジェクト

金額とその不変性・演算ルールをカプセル化します。
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Union


@dataclass(frozen=True)
class Money:
    """
    金額の値オブジェクト

    精度の問題を避けるため Decimal を使用し、
    金額に関する演算と不変条件を保証します。

    Attributes:
        amount: 金額（Decimal型、精度を保証）
        currency: 通貨コード（例: "JPY", "USD"）

    Raises:
        ValueError: 負の金額の場合（ビジネスルールに応じて調整可能）

    Examples:
        >>> price1 = Money(Decimal("1000.50"), "JPY")
        >>> price2 = Money(Decimal("500.25"), "JPY")
        >>> total = price1 + price2
        >>> total.amount
        Decimal('1500.75')
        >>> total.format()
        '¥1,500'
    """

    amount: Decimal
    currency: str = "JPY"

    def __post_init__(self):
        """
        初期化後のバリデーション

        Raises:
            ValueError: 負の金額の場合
        """
        if self.amount < 0:
            raise ValueError(f"Money amount cannot be negative: {self.amount}")

        # Decimal型に変換（文字列や数値から作成された場合）
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, "amount", Decimal(str(self.amount)))

    def __add__(self, other: "Money") -> "Money":
        """
        金額の加算

        Args:
            other: 加算する金額

        Returns:
            合計金額

        Raises:
            ValueError: 通貨が異なる場合
        """
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot add different currencies: {self.currency} and {other.currency}"
            )
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        """
        金額の減算

        Args:
            other: 減算する金額

        Returns:
            差額

        Raises:
            ValueError: 通貨が異なる場合、または結果が負になる場合
        """
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot subtract different currencies: {self.currency} and {other.currency}"
            )
        result = self.amount - other.amount
        if result < 0:
            raise ValueError(
                f"Cannot subtract {other.amount} from {self.amount}: result would be negative"
            )
        return Money(result, self.currency)

    def __mul__(self, multiplier: Union[int, float, Decimal]) -> "Money":
        """
        金額の乗算

        Args:
            multiplier: 乗数

        Returns:
            乗算後の金額
        """
        result = self.amount * Decimal(str(multiplier))
        return Money(result, self.currency)

    def __truediv__(self, divisor: Union[int, float, Decimal]) -> "Money":
        """
        金額の除算

        Args:
            divisor: 除数

        Returns:
            除算後の金額

        Raises:
            ZeroDivisionError: ゼロ除算の場合
        """
        if divisor == 0:
            raise ZeroDivisionError("Cannot divide money by zero")
        result = self.amount / Decimal(str(divisor))
        return Money(result, self.currency)

    def round(self, decimal_places: int = 0) -> "Money":
        """
        金額を指定された小数点以下の桁数で丸める（四捨五入）

        Args:
            decimal_places: 小数点以下の桁数（デフォルト: 0 = 整数）

        Returns:
            丸められた金額
        """
        quantize_str = "1" if decimal_places == 0 else f"0.{'0' * decimal_places}"
        rounded = self.amount.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)
        return Money(rounded, self.currency)

    def is_zero(self) -> bool:
        """ゼロかどうか"""
        return self.amount == 0

    def format(self, show_currency: bool = True) -> str:
        """
        金額を人間が読みやすい形式でフォーマット

        Args:
            show_currency: 通貨記号を表示するか

        Returns:
            フォーマットされた文字列（例: "¥1,234" または "1,234"）
        """
        # 日本円の場合は整数で表示
        if self.currency == "JPY":
            rounded = self.round(0)
            formatted = f"{rounded.amount:,.0f}"
            return f"¥{formatted}" if show_currency else formatted
        else:
            # その他の通貨は小数点2桁
            formatted = f"{self.amount:,.2f}"
            return f"{self.currency} {formatted}" if show_currency else formatted

    def __str__(self) -> str:
        """文字列表現"""
        return self.format()

    def __repr__(self) -> str:
        """デバッグ用表現"""
        return f"Money(amount={self.amount!r}, currency={self.currency!r})"

    def __eq__(self, other: object) -> bool:
        """等価性の比較"""
        if not isinstance(other, Money):
            return False
        return self.amount == other.amount and self.currency == other.currency

    def __lt__(self, other: "Money") -> bool:
        """小なり比較"""
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare different currencies")
        return self.amount < other.amount

    def __le__(self, other: "Money") -> bool:
        """小なりイコール比較"""
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare different currencies")
        return self.amount <= other.amount

    def __gt__(self, other: "Money") -> bool:
        """大なり比較"""
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare different currencies")
        return self.amount > other.amount

    def __ge__(self, other: "Money") -> bool:
        """大なりイコール比較"""
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare different currencies")
        return self.amount >= other.amount
