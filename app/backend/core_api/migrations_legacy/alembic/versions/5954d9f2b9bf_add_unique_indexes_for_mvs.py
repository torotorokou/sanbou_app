"""add_unique_indexes_for_mvs

Purpose:
  Add UNIQUE indexes to materialized views to enable REFRESH CONCURRENTLY.

Context:
  - REFRESH MATERIALIZED VIEW CONCURRENTLY requires a UNIQUE index
  - Previous migration (20251211_170000000) dropped and recreated MVs but forgot to recreate indexes
  - Without UNIQUE index, MV refresh fails with permission error

Changes:
  - Add UNIQUE index on mart.mv_receive_daily (ddate)
  - Add UNIQUE index on mart.mv_target_card_per_day (ddate)

Safety:
  - Indexes are idempotent (IF NOT EXISTS)
  - No data changes
  - Enables background refresh without blocking reads

Revision ID: 5954d9f2b9bf
Revises: 20251211_180000000
Create Date: 2025-12-12 09:35:48.718551

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5954d9f2b9bf"
down_revision = "20251211_180000000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add UNIQUE indexes to materialized views for REFRESH CONCURRENTLY support
    """
    print("[mart.mv_receive_daily] Creating UNIQUE index for REFRESH CONCURRENTLY...")

    # UNIQUE index on mv_receive_daily (primary key: ddate)
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_receive_daily_ddate
        ON mart.mv_receive_daily (ddate);
    """
    )

    # Regular index on iso_week for weekly queries
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_mv_receive_daily_iso_week
        ON mart.mv_receive_daily (iso_year, iso_week);
    """
    )

    print("[mart.mv_receive_daily] ✅ Indexes created")

    print(
        "[mart.mv_target_card_per_day] Creating UNIQUE index for REFRESH CONCURRENTLY..."
    )

    # UNIQUE index on mv_target_card_per_day (primary key: ddate)
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_target_card_per_day_ddate
        ON mart.mv_target_card_per_day (ddate);
    """
    )

    print("[mart.mv_target_card_per_day] ✅ Indexes created")
    print("")
    print("📌 Summary:")
    print("  - UNIQUE indexes added to enable REFRESH MATERIALIZED VIEW CONCURRENTLY")
    print("  - MVs can now be refreshed without blocking reads")
    print("  - CSV upload process will automatically refresh MVs")


def downgrade() -> None:
    """
    Remove UNIQUE indexes from materialized views
    """
    print("[mart.mv_receive_daily] Dropping indexes...")

    op.execute("DROP INDEX IF EXISTS mart.ux_mv_receive_daily_ddate;")
    op.execute("DROP INDEX IF EXISTS mart.ix_mv_receive_daily_iso_week;")

    print("[mart.mv_target_card_per_day] Dropping indexes...")

    op.execute("DROP INDEX IF EXISTS mart.ux_mv_target_card_per_day_ddate;")

    print("✅ Indexes dropped")
