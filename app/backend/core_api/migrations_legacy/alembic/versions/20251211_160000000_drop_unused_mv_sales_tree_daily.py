"""drop unused mv_sales_tree_daily materialized view

Purpose:
  Drop the obsolete mart.mv_sales_tree_daily materialized view that is
  no longer used after migration to mart.v_sales_tree_detail_base.

Context:
  - mv_sales_tree_daily was created in 20251125_120000000
  - v_sales_tree_daily was refactored in 20251201_110000000 to use v_sales_tree_detail_base
  - SalesTreeRepository uses v_sales_tree_detail_base directly
  - No Python code references mv_sales_tree_daily

Verification:
  - grep search: No references in app/backend/core_api/app/infra/adapters/
  - v_sales_tree_daily: Now references v_sales_tree_detail_base (not mv_sales_tree_daily)
  - v_customer_sales_daily: Depends on v_sales_tree_daily (not mv_sales_tree_daily)

Safety:
  - No dependent objects (CASCADE not needed)
  - Data size: 24 KB (minimal impact)
  - No auto-refresh configuration in MaterializedViewRefresher

Revision ID: 20251211_160000000
Revises: 20251211_150000000
Create Date: 2025-12-11 16:00:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251211_160000000"
down_revision = "20251211_150000000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Drop mv_sales_tree_daily materialized view
    """
    print("[mart.mv_sales_tree_daily] Dropping unused materialized view...")

    # Drop indexes explicitly (will be dropped with MV, but document for clarity)
    op.execute("DROP INDEX IF EXISTS mart.idx_mv_sales_tree_daily_composite;")
    op.execute("DROP INDEX IF EXISTS mart.idx_mv_sales_tree_daily_slip;")

    # Drop materialized view
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mart.mv_sales_tree_daily;")

    print("[ok] mv_sales_tree_daily dropped successfully")


def downgrade() -> None:
    """
    Recreate mv_sales_tree_daily from v_sales_tree_detail_base

    Note: This is for migration reversibility only.
    In practice, we don't want to restore this unused MV.
    """
    print("[mart.mv_sales_tree_daily] Recreating from v_sales_tree_detail_base...")

    op.execute(
        """
        CREATE MATERIALIZED VIEW mart.mv_sales_tree_daily AS
        SELECT * FROM mart.v_sales_tree_detail_base
        WITH NO DATA;
    """
    )

    op.execute(
        """
        CREATE INDEX idx_mv_sales_tree_daily_composite
        ON mart.mv_sales_tree_daily (sales_date, rep_id, customer_id, item_id);
    """
    )

    op.execute(
        """
        CREATE INDEX idx_mv_sales_tree_daily_slip
        ON mart.mv_sales_tree_daily (sales_date, customer_id, slip_no);
    """
    )

    print("[ok] mv_sales_tree_daily recreated (not refreshed)")
