"""
Date Range Value Object - 日付範囲を表す値オブジェクト

ビジネスルールを持つ不変の日付範囲。
開始日・終了日の妥当性検証と、範囲に関する問い合わせメソッドを提供します。
"""
from datetime import date, timedelta
from typing import Iterator
from dataclasses import dataclass


@dataclass(frozen=True)
class DateRange:
    """
    日付範囲の値オブジェクト
    
    不変性を保証し、日付範囲に関するビジネスルールを集約します。
    
    Attributes:
        start: 開始日（含む）
        end: 終了日（含む）
        
    Raises:
        ValueError: 開始日が終了日より後の場合
        
    Examples:
        >>> from datetime import date
        >>> range1 = DateRange(date(2025, 1, 1), date(2025, 1, 31))
        >>> range1.days()
        31
        >>> range1.contains(date(2025, 1, 15))
        True
        >>> range1.overlaps(DateRange(date(2025, 1, 20), date(2025, 2, 10)))
        True
    """
    start: date
    end: date
    
    def __post_init__(self):
        """
        初期化後のバリデーション
        
        Raises:
            ValueError: 開始日が終了日より後の場合
        """
        if self.start > self.end:
            raise ValueError(
                f"Invalid date range: start ({self.start}) must be <= end ({self.end})"
            )
    
    def days(self) -> int:
        """
        範囲の日数を返す（開始日・終了日を含む）
        
        Returns:
            日数（1以上）
        """
        return (self.end - self.start).days + 1
    
    def contains(self, target_date: date) -> bool:
        """
        指定された日付が範囲内に含まれるか判定
        
        Args:
            target_date: 判定対象の日付
            
        Returns:
            範囲内なら True、範囲外なら False
        """
        return self.start <= target_date <= self.end
    
    def overlaps(self, other: "DateRange") -> bool:
        """
        他の日付範囲と重複するか判定
        
        Args:
            other: 比較対象の日付範囲
            
        Returns:
            重複する場合 True、しない場合 False
        """
        return self.start <= other.end and other.start <= self.end
    
    def dates(self) -> Iterator[date]:
        """
        範囲内の全日付を順次返すイテレータ
        
        Yields:
            範囲内の日付（開始日から終了日まで）
            
        Examples:
            >>> range1 = DateRange(date(2025, 1, 1), date(2025, 1, 3))
            >>> list(range1.dates())
            [date(2025, 1, 1), date(2025, 1, 2), date(2025, 1, 3)]
        """
        current = self.start
        while current <= self.end:
            yield current
            current += timedelta(days=1)
    
    def is_single_day(self) -> bool:
        """
        単一日（開始日と終了日が同じ）かどうか
        
        Returns:
            単一日なら True、複数日なら False
        """
        return self.start == self.end
    
    def __str__(self) -> str:
        """文字列表現"""
        return f"{self.start} to {self.end} ({self.days()} days)"
    
    def __repr__(self) -> str:
        """デバッグ用表現"""
        return f"DateRange(start={self.start!r}, end={self.end!r})"
