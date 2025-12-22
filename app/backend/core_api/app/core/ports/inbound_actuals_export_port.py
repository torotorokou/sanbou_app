"""
Inbound Actuals Export Port

品目別日次実績データのエクスポート抽象インターフェース。
予測モデルの学習用データ（CSV形式）を生成するために使用。
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


class InboundActualsExportPort(ABC):
    """品目別日次実績データのエクスポートインターフェース"""
    
    @abstractmethod
    def export_item_level_actuals(
        self,
        start_date: date,
        end_date: date
    ) -> "pd.DataFrame":
        """
        指定期間の品目別日次実績を取得（日本語ヘッダ形式）
        
        Args:
            start_date: 開始日（この日を含む）
            end_date: 終了日（この日を含む）
        
        Returns:
            DataFrame with columns:
                - 伝票日付: date型（YYYY-MM-DD）
                - 品名: str（品目名）
                - 正味重量: float（ton単位）
        
        Notes:
            - stg.shogun_final_receive から取得
            - is_deleted=false のみ
            - net_weight（kg）を ton に変換して返す
            - 伝票日付, 品名 でソート
        """
        pass
