"""
Inbound UseCase DTO definitions

Input/Output DTOを明確に定義し、UseCase層とPresentation層の境界を明確にする
"""
from dataclasses import dataclass
from datetime import date as date_type
from typing import List, Optional

from app.core.domain.inbound.entities import InboundDailyRow, CumScope


# ========================================================================
# Input DTOs
# ========================================================================

@dataclass(frozen=True)
class GetInboundDailyInput:
    """
    日次搬入量データ取得UseCase - Input DTO
    
    Attributes:
        start: 開始日（必須）
        end: 終了日（必須）
        segment: セグメントフィルタ（オプション、None=全体）
        cum_scope: 累積計算スコープ（range|month|week|none）
    """
    start: date_type
    end: date_type
    segment: Optional[str] = None
    cum_scope: CumScope = "none"
    
    def validate(self) -> None:
        """
        入力値のバリデーション
        
        Raises:
            ValueError: バリデーションエラー
        """
        if self.start > self.end:
            raise ValueError(
                f"start date ({self.start}) must be <= end date ({self.end})"
            )
        
        delta_days = (self.end - self.start).days + 1
        if delta_days > 366:
            raise ValueError(
                f"Date range exceeds 366 days: {delta_days} days"
            )


# ========================================================================
# Output DTOs
# ========================================================================

@dataclass(frozen=True)
class GetInboundDailyOutput:
    """
    日次搬入量データ取得UseCase - Output DTO
    
    Attributes:
        data: 日次搬入量データのリスト（カレンダー連続・0埋め済み）
        total_count: データ件数
        date_range_days: 日付範囲（日数）
    """
    data: List[InboundDailyRow]
    total_count: int
    date_range_days: int
    
    @classmethod
    def from_domain(
        cls,
        data: List[InboundDailyRow],
        start: date_type,
        end: date_type,
    ) -> "GetInboundDailyOutput":
        """
        ドメインモデルからOutput DTOを生成
        
        Args:
            data: 日次搬入量データのリスト
            start: 開始日
            end: 終了日
            
        Returns:
            GetInboundDailyOutput
        """
        date_range_days = (end - start).days + 1
        return cls(
            data=data,
            total_count=len(data),
            date_range_days=date_range_days,
        )
