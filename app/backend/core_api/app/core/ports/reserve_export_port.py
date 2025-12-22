"""
Reserve Export Port

日次予約データのエクスポート抽象インターフェース。
予測モデルの入力データ（CSV形式）を生成するために使用。
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


class ReserveExportPort(ABC):
    """日次予約データのエクスポートインターフェース"""
    
    @abstractmethod
    def export_daily_reserve(
        self,
        start_date: date,
        end_date: date
    ) -> "pd.DataFrame":
        """
        指定期間の日次予約データを取得（日本語ヘッダ形式）
        
        Args:
            start_date: 開始日（この日を含む）
            end_date: 終了日（この日を含む）
        
        Returns:
            DataFrame with columns:
                - 予約日: date型（YYYY-MM-DD）
                - 台数: int（予約台数）
                - 固定客: int（固定客予約台数）
        
        Notes:
            - mart.v_reserve_daily_for_forecast から取得
            - 予約日でソート
        """
        pass
