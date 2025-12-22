"""
ReserveDailyRepositoryPort: 予約データの取得
===========================================
日次予約データを取得するためのポート（抽象インターフェース）
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List


@dataclass
class ReserveDailyForForecast:
    """予約データ（1日分）"""
    date: date
    reserve_trucks: int  # 予約台数合計
    total_customer_count: int  # 予約企業数（総数）
    fixed_customer_count: int  # 固定客企業数
    reserve_fixed_trucks: int  # 固定客台数
    reserve_fixed_ratio: Decimal  # 固定客比率 (0.0～1.0)
    source: str  # 'manual' or 'customer_agg'


class ReserveDailyRepositoryPort(ABC):
    """予約データの取得ポート"""
    
    @abstractmethod
    def get_reserve_daily(
        self,
        from_date: date,
        to_date: date,
    ) -> List[ReserveDailyForForecast]:
        """
        指定期間の予約データを取得
        
        Args:
            from_date: 開始日（この日を含む）
            to_date: 終了日（この日を含む）
        
        Returns:
            List[ReserveDailyForForecast]: 日付昇順のリスト（データが無い日は含まれない）
        
        Raises:
            Exception: DB接続エラー等
        """
        pass
