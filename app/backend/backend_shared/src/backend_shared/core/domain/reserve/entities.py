# app/backend/backend_shared/src/backend_shared/core/domain/reserve/entities.py
"""
Reserve domain entities.

予約データのドメインエンティティ定義。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class ReserveDailyForForecast:
    """
    予測用日次予約データ
    
    mart.v_reserve_daily_for_forecast から取得されるデータ。
    手動入力データと顧客別予約の集計データを統合したもの。
    
    Attributes:
        date: 予約日
        reserve_trucks: 予約台数合計
        reserve_fixed_trucks: 固定顧客の予約台数
        reserve_fixed_ratio: 固定顧客比率 (0.0-1.0)
        source: データソース ('manual' or 'customer_agg')
    """
    
    date: date
    reserve_trucks: int
    reserve_fixed_trucks: int
    reserve_fixed_ratio: Decimal
    source: str
