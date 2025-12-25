"""
Target card domain logic: Pure computation for target card data.
No side effects, no I/O.
"""

from datetime import date as date_type
from decimal import Decimal, InvalidOperation
from typing import Any, Literal

Mode = Literal["daily", "monthly"]

# ビジネス定数
ACHIEVEMENT_RATE_PRECISION = 1  # 達成率の小数点以下桁数
PERCENTAGE_MULTIPLIER = 100  # パーセンテージ変換用


def validate_target_card_date(
    requested_date: date_type, mode: Mode
) -> tuple[bool, str]:
    """
    Validate if the requested date is appropriate for the given mode.

    ビジネスルール:
      - monthly モードの場合、日付は月初（1日）でなければならない
      - daily モードの場合、任意の日付が許可される

    Args:
        requested_date: The date requested
        mode: "daily" or "monthly"

    Returns:
        tuple[bool, str]: (is_valid, error_message)
            - is_valid: True if valid, False otherwise
            - error_message: 空文字列（valid時）または具体的なエラーメッセージ
    """
    if mode == "monthly" and requested_date.day != 1:
        return (
            False,
            f"月次モードでは日付は月初（1日）でなければなりません（指定: {requested_date}）",
        )

    return True, ""


def calculate_achievement_rate(actual: float, target: float) -> float | None:
    """
    達成率を計算（ビジネスロジック）

    達成率 = (実績 / 目標) × 100

    Args:
        actual: 実績値
        target: 目標値

    Returns:
        float: 達成率（パーセンテージ）、目標が0の場合はNone
    """
    if target == 0:
        return None

    rate = (actual / target) * PERCENTAGE_MULTIPLIER
    return round(rate, ACHIEVEMENT_RATE_PRECISION)


def calculate_variance(actual: float, target: float) -> float:
    """
    差異を計算（実績 - 目標）

    Args:
        actual: 実績値
        target: 目標値

    Returns:
        float: 差異（正: 超過、負: 未達）
    """
    return round(actual - target, 2)


def transform_target_card_data(
    raw_data: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """
    Transform raw repository data into presentation format.
    Pure function: no side effects.

    変換処理:
      1. 達成率の計算（実績/目標）
      2. 差異の計算（実績-目標）
      3. 数値の精度調整
      4. 警告フラグの追加（閾値ベース）

    Args:
        raw_data: Raw data from repository
            Expected keys: target_value, actual_value, date, mode

    Returns:
        Transformed data suitable for API response, or None
    """
    if not raw_data:
        return None

    # Copy to avoid mutation
    transformed = raw_data.copy()

    # Extract target and actual
    target = raw_data.get("target_value")
    actual = raw_data.get("actual_value")

    if target is not None and actual is not None:
        try:
            # Convert to float if needed
            target_val = float(target)
            actual_val = float(actual)

            # Calculate achievement rate
            achievement_rate = calculate_achievement_rate(actual_val, target_val)
            if achievement_rate is not None:
                transformed["achievement_rate"] = achievement_rate

                # Add warning flags based on thresholds
                if achievement_rate < 80.0:
                    transformed["_warning"] = "low_achievement"
                elif achievement_rate > 120.0:
                    transformed["_warning"] = "high_achievement"

            # Calculate variance
            variance = calculate_variance(actual_val, target_val)
            transformed["variance"] = variance

        except (ValueError, TypeError, InvalidOperation) as e:
            # Log error but don't fail the transformation
            transformed["_error"] = f"calculation_error: {str(e)}"

    return transformed


def format_target_card_value(value: Any, decimal_places: int = 2) -> float | None:
    """
    目標カード用の数値フォーマット

    Args:
        value: フォーマット対象の値
        decimal_places: 小数点以下の桁数

    Returns:
        float: フォーマット済み数値、変換できない場合はNone
    """
    if value is None:
        return None

    try:
        if isinstance(value, Decimal):
            return round(float(value), decimal_places)
        return round(float(value), decimal_places)
    except (ValueError, TypeError, InvalidOperation):
        return None
