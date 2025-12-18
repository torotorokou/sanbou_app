"""
Reserve Exporter

日次予約データをDBから取得し、予測モデル用CSV形式で提供。
"""
from __future__ import annotations
from datetime import date
from typing import TYPE_CHECKING

import pandas as pd
from sqlalchemy import text

from app.core.ports.reserve_export_port import ReserveExportPort

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class ReserveExporter(ReserveExportPort):
    """日次予約エクスポーター（mart.v_reserve_daily_for_forecast）"""
    
    def __init__(self, db: "Session"):
        self.db = db
    
    def export_daily_reserve(
        self,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        指定期間の日次予約データを取得（日本語ヘッダ形式）
        
        Args:
            start_date: 開始日（この日を含む）
            end_date: 終了日（この日を含む）
        
        Returns:
            DataFrame with columns: [予約日, 台数, 固定客]
        
        Notes:
            - mart.v_reserve_daily_for_forecast から取得
            - 予約日でソート
        """
        sql = text("""
            SELECT 
                date AS "予約日",
                reserve_trucks AS "台数",
                reserve_fixed_trucks AS "固定客"
            FROM mart.v_reserve_daily_for_forecast
            WHERE date >= :start_date 
              AND date <= :end_date
            ORDER BY date
        """)
        
        result = self.db.execute(
            sql,
            {"start_date": start_date, "end_date": end_date}
        )
        
        rows = result.fetchall()
        
        return pd.DataFrame(
            rows,
            columns=["予約日", "台数", "固定客"]
        )
