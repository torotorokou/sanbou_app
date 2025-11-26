"""
Customer Churn Port

顧客離脱分析のためのPort（抽象インターフェース）
Clean Architectureのポート&アダプターパターンに準拠
"""
from typing import Protocol
from datetime import date as date_type

from app.domain.entities.customer_churn import LostCustomer


class CustomerChurnQueryPort(Protocol):
    """顧客離脱分析クエリのPort"""

    def find_lost_customers(
        self,
        current_start: date_type,
        current_end: date_type,
        previous_start: date_type,
        previous_end: date_type,
    ) -> list[LostCustomer]:
        """
        離脱顧客を検索
        
        前期間（previous_start ~ previous_end）には来ていたが、
        今期間（current_start ~ current_end）には1回も来ていない顧客を返す。
        
        Args:
            current_start: 今期間の開始日
            current_end: 今期間の終了日
            previous_start: 前期間の開始日
            previous_end: 前期間の終了日
            
        Returns:
            list[LostCustomer]: 離脱顧客のリスト（last_visit_date降順）
        """
        ...
