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
    """日次予測結果
    
    統計的定義（Phase 2以降）:
    - p50（median）: 中央値（50%分位点、Quantile回帰 alpha=0.5）
    - p10（lower_1sigma）: 下側区間（median - 1.28σ、正規分布仮定、真の10%分位点ではない）
    - p90（upper_quantile_90）: 上側90%分位点（Quantile回帰 alpha=0.9）
    
    Note:
        パラメータ名は互換性のためp50/p10/p90だが、実態は上記の統計的意味を持つ。
        DBには新カラム（median, lower_1sigma, upper_quantile_90）と
        旧カラム（p50, p10, p90）の両方に保存される。
    """
    target_date: date
    job_id: UUID
    p50: Decimal  # median: 中央値（50%分位点）
    p10: Optional[Decimal] = None  # lower_1sigma: median - 1.28σ（正規分布仮定）
    p90: Optional[Decimal] = None  # upper_quantile_90: 90%分位点
    unit: str = "kg"
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
