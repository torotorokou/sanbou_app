"""create mart sales tree views (v_sales_tree_daily, v_customer_sales_daily)

Revision ID: 20251125_150000000
Revises: 20251125_140000000
Create Date: 2025-11-25 23:27:17.737401

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251125_150000000"
down_revision = "20251125_140000000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create mart sales tree views

    Purpose: Query interface for sales tree analysis
    Views:
    - mart.v_sales_tree_daily: wrapper for mv_sales_tree_daily
    - mart.v_customer_sales_daily: customer-level daily aggregation

    Depends on: mart.mv_sales_tree_daily (materialized view)
    """

    print("[mart] Creating v_sales_tree_daily view...")
    op.execute(
        """
        CREATE OR REPLACE VIEW mart.v_sales_tree_daily AS
        SELECT
            sales_date,
            rep_id,
            rep_name,
            customer_id,
            customer_name,
            item_id,
            item_name,
            amount_yen,
            qty_kg,
            slip_no,
            slip_count
        FROM mart.mv_sales_tree_daily
    """
    )

    print("[mart] Creating v_customer_sales_daily view...")
    op.execute(
        """
        CREATE OR REPLACE VIEW mart.v_customer_sales_daily AS
        SELECT
            sales_date,
            customer_id,
            MAX(customer_name) AS customer_name,
            MAX(rep_id) AS sales_rep_id,
            MAX(rep_name) AS sales_rep_name,
            COUNT(DISTINCT slip_no) AS visit_count,
            SUM(amount_yen) AS total_amount_yen,
            SUM(qty_kg) AS total_qty_kg
        FROM mart.v_sales_tree_daily v
        GROUP BY sales_date, customer_id
    """
    )

    print("[ok] mart sales tree views created")


def downgrade() -> None:
    """Drop mart sales tree views"""
    print("[mart] Dropping sales tree views...")
    op.execute("DROP VIEW IF EXISTS mart.v_customer_sales_daily")
    op.execute("DROP VIEW IF EXISTS mart.v_sales_tree_daily")
