"""recreate mv_target_card_per_day

Revision ID: 20251211_180000000
Revises: 20251211_175000000
Create Date: 2025-12-11 18:00:00.000000

"""

from pathlib import Path

import sqlalchemy as sa
from alembic import context, op

# .sql 正本の配置ディレクトリ
BASE = Path("/backend/migrations/alembic/sql/mart")

# revision identifiers, used by Alembic.
revision = "20251211_180000000"
down_revision = "20251211_175000000"
branch_labels = None
depends_on = None


def _exists(qualified: str) -> bool:
    """
    qualified: 'mart.mv_xxx' のようなスキーマ付オブジェクト名。
    オフライン(--sql)は常に False を返し、CREATE句を必ず出す（新規ブート用）。
    オンライン時のみ to_regclass で実在判定。
    """
    if context.is_offline_mode():
        return False
    conn = op.get_bind()
    return bool(
        conn.execute(
            sa.text("SELECT to_regclass(:q) IS NOT NULL"), {"q": qualified}
        ).scalar()
    )


def _read_sql(name_wo_ext: str) -> str:
    """SQL正本ファイル読み込み"""
    p = BASE / f"{name_wo_ext}.sql"
    with open(p, encoding="utf-8") as f:
        return f.read()


def upgrade() -> None:
    """
    Recreate mart.mv_target_card_per_day materialized view

    This MV was previously deleted by CASCADE during mv_receive_daily update.
    Now we recreate it with proper indexes for dashboard target card queries.
    """
    print("[mart.mv_target_card_per_day] Recreating materialized view...")

    if not _exists("mart.mv_target_card_per_day"):
        # Create materialized view from SQL file
        op.execute(_read_sql("mv_target_card_per_day"))

        # Create UNIQUE INDEX (required for REFRESH CONCURRENTLY)
        op.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_target_card_per_day_ddate
            ON mart.mv_target_card_per_day (ddate);
        """
        )

        # Create index for weekly aggregation
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS ix_mv_target_card_per_day_iso_week
            ON mart.mv_target_card_per_day (iso_year, iso_week);
        """
        )

        # Initial REFRESH
        print("[mart.mv_target_card_per_day] Refreshing materialized view...")
        op.execute("REFRESH MATERIALIZED VIEW mart.mv_target_card_per_day;")
    else:
        # If already exists, just refresh
        print("[mart.mv_target_card_per_day] Already exists, refreshing...")
        op.execute(
            "REFRESH MATERIALIZED VIEW CONCURRENTLY mart.mv_target_card_per_day;"
        )

    print("[mart.mv_target_card_per_day] ✅ Successfully recreated")


def downgrade() -> None:
    """
    Drop mart.mv_target_card_per_day materialized view
    """
    print("[mart.mv_target_card_per_day] Dropping materialized view...")

    # Drop indexes
    op.execute("DROP INDEX IF EXISTS mart.ix_mv_target_card_per_day_iso_week;")
    op.execute("DROP INDEX IF EXISTS mart.ux_mv_target_card_per_day_ddate;")

    # Drop materialized view
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mart.mv_target_card_per_day CASCADE;")

    print("[mart.mv_target_card_per_day] ✅ Dropped")
