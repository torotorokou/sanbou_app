"""create ref master views (customer, item, sales_rep)

Revision ID: 20251125_140000000
Revises: 20251125_130000000
Create Date: 2025-11-25 09:10:29.085908

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251125_140000000"
down_revision = "20251125_130000000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create ref master views for customer, item, and sales_rep

    Purpose: Extract master data from transactional data (stg.shogun_flash_receive)
    Views:
    - ref.v_customer: customer master with assigned sales rep
    - ref.v_item: item master with unit and category
    - ref.v_sales_rep: sales rep master

    Note: These views dynamically derive master data from active transactions
    """

    print("[ref] Creating v_customer view...")
    op.execute(
        """
        CREATE OR REPLACE VIEW ref.v_customer AS
        SELECT
            client_cd AS customer_id,
            MAX(client_name) AS customer_name,
            MAX(sales_staff_cd) AS sales_rep_id,
            MAX(sales_staff_name) AS sales_rep_name
        FROM stg.shogun_flash_receive s
        WHERE is_deleted = false
        GROUP BY client_cd
    """
    )

    print("[ref] Creating v_item view...")
    op.execute(
        """
        CREATE OR REPLACE VIEW ref.v_item AS
        SELECT
            item_cd AS item_id,
            MAX(item_name) AS item_name,
            MAX(unit_cd) AS unit_cd,
            MAX(unit_name) AS unit_name,
            MAX(category_cd) AS category_cd,
            MAX(category_name) AS category_name
        FROM stg.shogun_flash_receive s
        WHERE is_deleted = false
        GROUP BY item_cd
    """
    )

    print("[ref] Creating v_sales_rep view...")
    op.execute(
        """
        CREATE OR REPLACE VIEW ref.v_sales_rep AS
        SELECT
            sales_staff_cd AS sales_rep_id,
            MAX(sales_staff_name) AS sales_rep_name
        FROM stg.shogun_flash_receive s
        WHERE is_deleted = false
        GROUP BY sales_staff_cd
    """
    )

    print("[ok] ref master views created")


def downgrade() -> None:
    """Drop ref master views"""
    print("[ref] Dropping master views...")
    op.execute("DROP VIEW IF EXISTS ref.v_sales_rep")
    op.execute("DROP VIEW IF EXISTS ref.v_item")
    op.execute("DROP VIEW IF EXISTS ref.v_customer")
