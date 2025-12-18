"""
InboundActualRepositoryPort: 日次実績データの取得
================================================
日次搬入量の実績データを取得するためのポート（抽象インターフェース）
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List


@dataclass
class InboundActualDaily:
    """日次実績データ（1日分）"""
    ddate: date
    receive_net_ton: Decimal  # 受入量（トン）
    receive_vehicle_count: int  # 車両台数
    iso_year: int
    iso_week: int
    iso_dow: int  # 1=月, 7=日
    is_business: bool
    is_holiday: bool
    day_type: str  # 'NORMAL', 'SUNDAY', 'HOLIDAY'


class InboundActualRepositoryPort(ABC):
    """日次実績データの取得ポート"""
    
    @abstractmethod
    def get_daily_actuals(
        self,
        from_date: date,
        to_date: date,
    ) -> List[InboundActualDaily]:
        """
        指定期間の日次実績データを取得
        
        Args:
            from_date: 開始日（この日を含む）
            to_date: 終了日（この日を含む）
        
        Returns:
            List[InboundActualDaily]: 日付昇順のリスト
        
        Raises:
            Exception: DB接続エラー等
        """
        pass
