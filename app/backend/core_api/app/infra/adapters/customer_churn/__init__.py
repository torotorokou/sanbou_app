"""
Customer Churn Query Adapter

CustomerChurnQueryPortの実装
PostgreSQL/SQLAlchemyを使用して顧客離脱データを取得
"""
import logging
from typing import Optional
from datetime import date as date_type
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.domain.entities.customer_churn import LostCustomer

logger = logging.getLogger(__name__)


class CustomerChurnQueryAdapter:
    """
    顧客離脱分析クエリのAdapter（CustomerChurnQueryPort実装）
    
    mart.v_customer_sales_daily を使用して離脱顧客を検索する。
    """

    def __init__(self, db: Session):
        self.db = db

    def find_lost_customers(
        self,
        current_start: date_type,
        current_end: date_type,
        previous_start: date_type,
        previous_end: date_type,
    ) -> list[LostCustomer]:
        """
        離脱顧客を検索
        
        ロジック：
        - previous期間（比較基準期間）= 過去の基準期間に取引があった顧客を集計
        - current期間（最新期間）= 最近の期間に取引がある顧客をリスト化
        - 離脱顧客 = previous期間に取引があり、current期間に取引がない顧客
        
        例：
        - current: 2025-01-01 〜 2025-11-30（最新期間）
        - previous: 2024-01-01 〜 2024-12-31（比較基準期間）
        - 結果: 2024年に取引があったが、2025年に取引がない顧客 = 離脱顧客
        
        Args:
            current_start: 最新期間の開始日（この期間に取引がなければ「離脱」）
            current_end: 最新期間の終了日
            previous_start: 比較基準期間の開始日（この期間に取引があった顧客が対象）
            previous_end: 比較基準期間の終了日
            
        Returns:
            list[LostCustomer]: 離脱顧客のリスト（last_visit_date降順）
        """
        # SQL: previous期間（過去の基準）には存在するがcurrent期間（最新）には存在しない顧客を抽出
        sql = text("""
            WITH prev AS (
                -- 比較基準期間（previous）の顧客を集計
                SELECT
                    customer_id,
                    COUNT(*)                    AS prev_visit_days,
                    SUM(total_amount_yen)       AS prev_total_amount_yen,
                    SUM(total_qty_kg)           AS prev_total_qty_kg,
                    MAX(sales_date)             AS last_visit_date,
                    MAX(customer_name)          AS customer_name,
                    MAX(sales_rep_id)           AS sales_rep_id,
                    MAX(sales_rep_name)         AS sales_rep_name
                FROM mart.v_customer_sales_daily
                WHERE sales_date BETWEEN :previous_start AND :previous_end
                GROUP BY customer_id
            ),
            curr AS (
                -- 最新期間（current）の顧客リスト
                SELECT DISTINCT customer_id
                FROM mart.v_customer_sales_daily
                WHERE sales_date BETWEEN :current_start AND :current_end
            )
            SELECT
                p.customer_id,
                p.customer_name,
                p.sales_rep_id,
                p.sales_rep_name,
                p.last_visit_date,
                p.prev_visit_days,
                p.prev_total_amount_yen,
                p.prev_total_qty_kg
            FROM prev p
            LEFT JOIN curr c ON p.customer_id = c.customer_id
            WHERE c.customer_id IS NULL  -- 比較基準期間（previous）には存在するが、最新期間（current）には存在しない = 離脱
            ORDER BY p.last_visit_date DESC
        """)
        
        # デバッグログ
        logger.info(f"[CHURN QUERY] Parameters: current={current_start}~{current_end}, previous={previous_start}~{previous_end}")
        
        result = self.db.execute(
            sql,
            {
                "current_start": current_start,
                "current_end": current_end,
                "previous_start": previous_start,
                "previous_end": previous_end,
            },
        )
        
        rows = result.fetchall()
        logger.info(f"[CHURN QUERY] Found {len(rows)} lost customers")
        
        # デバッグ: 野呂商店を含む場合はログ出力
        for row in rows:
            if '野呂' in row.customer_name:
                logger.warning(
                    f"[CHURN QUERY] 野呂商店が離脱リストに含まれています: "
                    f"customer_id={row.customer_id}, name={row.customer_name}, "
                    f"last_visit={row.last_visit_date}"
                )
        
        lost_customers = []
        for row in rows:
            lost_customers.append(
                LostCustomer(
                    customer_id=row.customer_id,
                    customer_name=row.customer_name or "",
                    sales_rep_id=row.sales_rep_id,
                    sales_rep_name=row.sales_rep_name,
                    last_visit_date=row.last_visit_date,
                    prev_visit_days=row.prev_visit_days,
                    prev_total_amount_yen=float(row.prev_total_amount_yen or 0),
                    prev_total_qty_kg=float(row.prev_total_qty_kg or 0),
                )
            )
        
        return lost_customers


# Export for external use
__all__ = ['CustomerChurnQueryAdapter']
