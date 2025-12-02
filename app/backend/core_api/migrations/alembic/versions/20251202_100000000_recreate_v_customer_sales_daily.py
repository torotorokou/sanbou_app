"""recreate v_customer_sales_daily view

Revision ID: 20251202_100000000
Revises: 20251201_160000000
Create Date: 2024-12-02 10:00:00.000000

Issue: v_customer_sales_daily ビューが前回のマイグレーションで削除されたまま再作成されなかった

Solution:
- mart.v_customer_sales_daily ビューを再作成
- v_sales_tree_daily に依存

Note: このビューは顧客離脱分析（Customer Churn Analysis）で使用される
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251202_100000000'
down_revision = '20251201_160000000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Recreate mart.v_customer_sales_daily view
    """
    
    print("[mart] Recreating v_customer_sales_daily...")
    op.execute("DROP VIEW IF EXISTS mart.v_customer_sales_daily CASCADE")
    op.execute("""
        CREATE VIEW mart.v_customer_sales_daily AS
        SELECT
            sales_date,
            customer_id,
            MAX(customer_name) AS customer_name,
            MAX(rep_id) AS rep_id,
            MAX(rep_name) AS rep_name,
            COUNT(DISTINCT slip_no) AS visit_count,
            SUM(amount_yen) AS total_amount_yen,
            SUM(qty_kg) AS total_qty_kg,
            SUM(qty_kg) AS total_net_weight_kg  -- canonical alias
        FROM mart.v_sales_tree_daily v
        GROUP BY sales_date, customer_id
    """)
    
    print("[ok] v_customer_sales_daily view recreated")


def downgrade() -> None:
    """
    Drop mart.v_customer_sales_daily view
    """
    
    print("[mart] Dropping v_customer_sales_daily...")
    op.execute("DROP VIEW IF EXISTS mart.v_customer_sales_daily CASCADE")
    
    print("[ok] v_customer_sales_daily view dropped")
