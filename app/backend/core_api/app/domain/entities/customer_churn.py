"""
Customer Churn Domain Entities

顧客離脱分析のドメインエンティティ
"""
from dataclasses import dataclass
from datetime import date as date_type
from typing import Optional


@dataclass(frozen=True)
class LostCustomer:
    """
    離脱顧客エンティティ
    
    前期間には来ていたが、今期間には1回も来ていない顧客を表す。
    """
    customer_id: str
    customer_name: str
    rep_id: Optional[str]
    rep_name: Optional[str]
    last_visit_date: date_type
    prev_visit_days: int
    prev_total_amount_yen: float
    prev_total_qty_kg: float
    
    def __post_init__(self):
        """不変条件のバリデーション"""
        if self.prev_visit_days < 0:
            raise ValueError("prev_visit_days must be non-negative")
        if self.prev_total_amount_yen < 0:
            raise ValueError("prev_total_amount_yen must be non-negative")
        if self.prev_total_qty_kg < 0:
            raise ValueError("prev_total_qty_kg must be non-negative")
