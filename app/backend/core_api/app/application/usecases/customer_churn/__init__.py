"""
Customer Churn UseCase

顧客離脱分析のユースケース層
Clean Architectureに準拠し、Portを介してデータアクセスを行う
"""
from datetime import date as date_type

from app.domain.ports.customer_churn_port import CustomerChurnQueryPort
from app.domain.entities.customer_churn import LostCustomer


class AnalyzeCustomerChurnUseCase:
    """
    顧客離脱分析ユースケース
    
    前期間と今期間を比較して、離脱した顧客を特定する。
    """

    def __init__(self, query_port: CustomerChurnQueryPort):
        self.query_port = query_port

    def execute(
        self,
        current_start: date_type,
        current_end: date_type,
        previous_start: date_type,
        previous_end: date_type,
    ) -> list[LostCustomer]:
        """
        離脱顧客分析を実行
        
        Args:
            current_start: 今期間の開始日
            current_end: 今期間の終了日
            previous_start: 前期間の開始日
            previous_end: 前期間の終了日
            
        Returns:
            list[LostCustomer]: 離脱顧客のリスト
            
        Raises:
            ValueError: 期間指定が不正な場合
        """
        # バリデーション
        if current_start > current_end:
            raise ValueError("current_start must be <= current_end")
        if previous_start > previous_end:
            raise ValueError("previous_start must be <= previous_end")
        
        # Port経由でデータ取得（Clean Architectureの依存性逆転）
        return self.query_port.find_lost_customers(
            current_start=current_start,
            current_end=current_end,
            previous_start=previous_start,
            previous_end=previous_end,
        )


# Export for external use
__all__ = ['AnalyzeCustomerChurnUseCase']
