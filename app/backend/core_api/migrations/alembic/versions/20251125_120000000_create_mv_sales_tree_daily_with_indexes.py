"""create mv_sales_tree_daily with indexes

Revision ID: 20251125_120000000
Revises: 7e3d1c5e0036
Create Date: 2025-11-25 09:06:54.062832

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251125_120000000'
down_revision = '20251125_044600487'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create mart.mv_sales_tree_daily materialized view with indexes
    
    Purpose: Daily sales tree data materialized for performance
    Source: stg.shogun_flash_receive (category_cd = 1, waste only)
    Indexes:
    - Composite: (sales_date, rep_id, customer_id, item_id)
    - Slip: (sales_date, customer_id, slip_no)
    """
    
    print("[mart.mv_sales_tree_daily] Creating materialized view...")
    
    op.execute("""
        CREATE MATERIALIZED VIEW mart.mv_sales_tree_daily AS
        SELECT
            COALESCE(sales_date, slip_date) AS sales_date,
            sales_staff_cd AS rep_id,
            sales_staff_name AS rep_name,
            client_cd AS customer_id,
            client_name AS customer_name,
            item_cd AS item_id,
            item_name,
            amount AS amount_yen,
            net_weight AS qty_kg,
            receive_no AS slip_no,
            1 AS slip_count
        FROM stg.shogun_flash_receive
        WHERE category_cd = 1
          AND COALESCE(sales_date, slip_date) IS NOT NULL
          AND COALESCE(is_deleted, false) = false
    """)
    
    print("[mart.mv_sales_tree_daily] Creating composite index...")
    op.execute("""
        CREATE INDEX idx_mv_sales_tree_daily_composite
        ON mart.mv_sales_tree_daily (sales_date, rep_id, customer_id, item_id)
    """)
    
    print("[mart.mv_sales_tree_daily] Creating slip index...")
    op.execute("""
        CREATE INDEX idx_mv_sales_tree_daily_slip
        ON mart.mv_sales_tree_daily (sales_date, customer_id, slip_no)
    """)
    
    print("[ok] mv_sales_tree_daily created with indexes")


def downgrade() -> None:
    """Drop mart.mv_sales_tree_daily"""
    print("[mart.mv_sales_tree_daily] Dropping materialized view...")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mart.mv_sales_tree_daily")
