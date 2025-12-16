"""
Reservation repository port (abstract interface).
予約データの取得・更新のポート定義
"""
from abc import ABC, abstractmethod
from datetime import date as date_type
from typing import List, Optional

from app.core.domain.reservation import (
    ReservationManualRow,
    ReservationForecastRow,
    ReservationCustomerRow,
)


class ReservationRepository(ABC):
    """
    Reservation data repository interface.
    予約データ（手入力・顧客別・予測用ビュー）の取得・更新を抽象化
    """

    # ========================================
    # Manual (手入力) Operations
    # ========================================

    @abstractmethod
    def get_manual(self, reserve_date: date_type) -> Optional[ReservationManualRow]:
        """
        指定日の手入力予約データを取得
        
        Args:
            reserve_date: 予約日
        
        Returns:
            手入力データ（存在しない場合はNone）
        """
        pass

    @abstractmethod
    def upsert_manual(self, data: ReservationManualRow) -> ReservationManualRow:
        """
        手入力予約データを登録・更新
        
        Args:
            data: 手入力予約データ
        
        Returns:
            登録・更新されたデータ
        """
        pass

    @abstractmethod
    def delete_manual(self, reserve_date: date_type) -> bool:
        """
        指定日の手入力予約データを削除
        
        Args:
            reserve_date: 予約日
        
        Returns:
            削除成功時True、データが存在しなかった場合False
        """
        pass

    # ========================================
    # Forecast View (予測用) Operations
    # ========================================

    @abstractmethod
    def get_forecast_month(
        self, year: int, month: int
    ) -> List[ReservationForecastRow]:
        """
        指定月の予測用予約データを取得（manual優先、なければcustomer集計）
        
        Args:
            year: 年
            month: 月
        
        Returns:
            予測用日次予約データのリスト（mart.v_reserve_daily_for_forecast）
        """
        pass
