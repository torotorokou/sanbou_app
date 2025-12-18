"""
ForecastResultRepositoryPort: 予測結果の保存
===========================================
日次予測結果をDBに保存するためのポート（抽象インターフェース）
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Optional
from uuid import UUID


@dataclass
class DailyForecastResult:
    """日次予測結果"""
    target_date: date
    job_id: UUID
    p50: Decimal  # 中央値予測（メイン）
    p10: Optional[Decimal] = None  # 下側予測
    p90: Optional[Decimal] = None  # 上側予測
    unit: str = "ton"
    input_snapshot: Optional[Dict] = None


class ForecastResultRepositoryPort(ABC):
    """予測結果の保存ポート"""
    
    @abstractmethod
    def save_daily_forecast(
        self,
        result: DailyForecastResult
    ) -> UUID:
        """
        日次予測結果をDBに保存
        
        Args:
            result: 予測結果
        
        Returns:
            UUID: 保存された結果のID
        
        Raises:
            Exception: DB接続エラー、制約違反等
        """
        pass
