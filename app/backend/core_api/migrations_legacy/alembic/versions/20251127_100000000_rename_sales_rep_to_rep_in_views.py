"""rename sales_rep to rep in views

Revision ID: 20251127_100000000
Revises: 20251125_150000000
Create Date: 2025-11-27 10:00:00.000000

Description:
    営業担当者カラムの命名を統一:
    - sales_rep_id → rep_id
    - sales_rep_name → rep_name

    影響範囲:
    - ref.v_sales_rep
    - mart.v_customer_sales_daily

    目的:
    - Sales Pivot機能との命名統一
    - API/フロントエンド全体での一貫性確保
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251127_100000000"
down_revision = "20251125_150000000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Rename sales_rep_* to rep_* in views"""

    print("[ref] Dropping and recreating v_sales_rep view with rep_id, rep_name...")
    op.execute("DROP VIEW IF EXISTS ref.v_sales_rep CASCADE")
    op.execute(
        """
        CREATE VIEW ref.v_sales_rep AS
        SELECT
            sales_staff_cd AS rep_id,
            MAX(sales_staff_name) AS rep_name
        FROM stg.shogun_flash_receive s
        WHERE is_deleted = false
        GROUP BY sales_staff_cd
    """
    )

    print(
        "[mart] Dropping and recreating v_customer_sales_daily view with rep_id, rep_name..."
    )
    op.execute("DROP VIEW IF EXISTS mart.v_customer_sales_daily CASCADE")
    op.execute(
        """
        CREATE VIEW mart.v_customer_sales_daily AS
        SELECT
            sales_date,
            customer_id,
            MAX(customer_name) AS customer_name,
            MAX(rep_id) AS rep_id,
            MAX(rep_name) AS rep_name,
            COUNT(DISTINCT slip_no) AS visit_count,
            SUM(amount_yen) AS total_amount_yen,
            SUM(qty_kg) AS total_qty_kg
        FROM mart.v_sales_tree_daily v
        GROUP BY sales_date, customer_id
    """
    )

    print("[ok] Views updated with unified rep_id/rep_name naming")


def downgrade() -> None:
    """Revert to sales_rep_* naming"""

    print(
        "[mart] Dropping and recreating v_customer_sales_daily view with sales_rep_id, sales_rep_name..."
    )
    op.execute("DROP VIEW IF EXISTS mart.v_customer_sales_daily CASCADE")
    op.execute(
        """
        CREATE VIEW mart.v_customer_sales_daily AS
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

    print(
        "[ref] Dropping and recreating v_sales_rep view with sales_rep_id, sales_rep_name..."
    )
    op.execute("DROP VIEW IF EXISTS ref.v_sales_rep CASCADE")
    op.execute(
        """
        CREATE VIEW ref.v_sales_rep AS
        SELECT
            sales_staff_cd AS sales_rep_id,
            MAX(sales_staff_name) AS sales_rep_name
        FROM stg.shogun_flash_receive s
        WHERE is_deleted = false
        GROUP BY sales_staff_cd
    """
    )

    print("[ok] Views reverted to sales_rep_* naming")
