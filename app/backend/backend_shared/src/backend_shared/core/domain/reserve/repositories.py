# app/backend/backend_shared/src/backend_shared/core/domain/reserve/repositories.py
"""
Reserve repository interface (Port).

予約データリポジトリの抽象インターフェース。
Clean Architecture における Port（外部システムとの境界）。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from backend_shared.core.domain.reserve.entities import ReserveDailyForForecast


class ReserveRepository(ABC):
    """
    予約データリポジトリインターフェース
    
    予測用の予約データを取得するための抽象リポジトリ。
    実装は infrastructure 層で行う。
    """
    
    @abstractmethod
    def get_reserve_daily_for_forecast(
        self,
        from_date: date,
        to_date: date,
    ) -> list[ReserveDailyForForecast]:
        """
        予測用日次予約データを取得
        
        mart.v_reserve_daily_for_forecast から指定期間のデータを取得する。
        
        Args:
            from_date: 開始日（この日を含む）
            to_date: 終了日（この日を含む）
        
        Returns:
            list[ReserveDailyForForecast]: 予約データのリスト（日付昇順）
        
        Raises:
            DatabaseError: DB接続エラー時
        """
        raise NotImplementedError
