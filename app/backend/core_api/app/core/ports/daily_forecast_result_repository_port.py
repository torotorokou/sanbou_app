"""
Daily Forecast Result Repository Port

日次予測結果の保存インターフェース。
forecast.daily_forecast_results テーブルへのデータ永続化を抽象化。
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID
from typing import Optional, Dict, Any


class DailyForecastResultRepositoryPort(ABC):
    """日次予測結果のリポジトリインターフェース"""
    
    @abstractmethod
    def save_result(
        self,
        target_date: date,
        job_id: UUID,
        p50: float,
        p10: Optional[float],
        p90: Optional[float],
        unit: str,
        input_snapshot: Dict[str, Any]
    ) -> UUID:
        """
        日次予測結果を保存
        
        Args:
            target_date: 予測対象日（t+1）
            job_id: forecast.forecast_jobs.id
            p50: 中央値予測（メイン）
            p10: 10パーセンタイル（下側予測、Noneも可）
            p90: 90パーセンタイル（上側予測、Noneも可）
            unit: 単位（'ton' or 'kg'）
            input_snapshot: 入力データ詳細（JSON）
        
        Returns:
            保存されたレコードのID
        
        Raises:
            IntegrityError: UNIQUE制約違反（同一 target_date, job_id）
        
        Notes:
            - forecast.daily_forecast_results に INSERT
            - UNIQUE (target_date, job_id) 制約あり
            - generated_at は自動設定
        """
        pass
