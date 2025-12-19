"""
Inbound Actuals Exporter

品目別日次実績データをDBから取得し、予測モデル用CSV形式で提供。
"""
from __future__ import annotations
from datetime import date
from typing import TYPE_CHECKING

import pandas as pd
from sqlalchemy import text

from app.core.ports.inbound_actuals_export_port import InboundActualsExportPort

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class InboundActualsExporter(InboundActualsExportPort):
    """品目別日次実績エクスポーター（stg.shogun_final_receive）"""
    
    def __init__(self, db: "Session"):
        self.db = db
    
    def export_item_level_actuals(
        self,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        指定期間の品目別日次実績を取得（日本語ヘッダ形式）
        
        Args:
            start_date: 開始日（この日を含む）
            end_date: 終了日（この日を含む）
        
        Returns:
            DataFrame with columns: [伝票日付, 品名, 正味重量]
            正味重量は kg 単位
        
        Notes:
            - stg.v_active_shogun_flash_receive から取得（is_deleted=falseのみ）
            - kg 単位（変換なし）
            - net_weight IS NOT NULL のみ
        """
        sql = text("""
            SELECT 
                slip_date AS "伝票日付",
                item_name AS "品名",
                net_weight AS "正味重量"
            FROM stg.v_active_shogun_flash_receive
            WHERE slip_date >= :start_date 
              AND slip_date <= :end_date
              AND net_weight IS NOT NULL
              AND item_name IS NOT NULL
            ORDER BY slip_date, item_name
        """)
        
        result = self.db.execute(
            sql,
            {"start_date": start_date, "end_date": end_date}
        )
        
        rows = result.fetchall()
        
        return pd.DataFrame(
            rows,
            columns=["伝票日付", "品名", "正味重量"]
        )
