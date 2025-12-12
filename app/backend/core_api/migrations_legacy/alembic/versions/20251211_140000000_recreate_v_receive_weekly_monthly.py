"""recreate v_receive_weekly and v_receive_monthly views

Purpose:
  Recreate the weekly and monthly receive aggregation VIEWs that were
  dropped due to CASCADE when dropping mart.v_receive_daily.

Context:
  - These VIEWs now reference mart.mv_receive_daily instead of v_receive_daily
  - SQL definitions updated in sql/mart/v_receive_weekly.sql and v_receive_monthly.sql

Dependencies:
  - Requires mart.mv_receive_daily to exist (created in 20251211_120000000)

Revision ID: 20251211_140000000
Revises: 20251211_130000000
Create Date: 2025-12-11 14:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from pathlib import Path


# revision identifiers, used by Alembic.
revision = '20251211_140000000'
down_revision = '20251211_130000000'
branch_labels = None
depends_on = None


BASE = Path("/backend/migrations/alembic/sql/mart")


def _read_sql(name: str) -> str:
    """Read SQL file content"""
    p = BASE / name
    with open(p, "r", encoding="utf-8") as f:
        return f.read()


def _check_mv_exists() -> None:
    """
    Check if mart.mv_receive_daily exists before creating dependent views.
    
    Raises:
        RuntimeError: If mart.mv_receive_daily does not exist
    """
    conn = op.get_bind()
    result = conn.execute(text("SELECT to_regclass('mart.mv_receive_daily')")).scalar()
    
    if result is None:
        raise RuntimeError(
            "❌ mart.mv_receive_daily is missing before creating v_receive_weekly/monthly.\n"
            "   This migration depends on 20251211_120000000_create_mv_receive_daily.\n"
            "   Please ensure that migration completed successfully."
        )
    
    print(f"  ✓ Verified mart.mv_receive_daily exists (oid: {result})")


def upgrade() -> None:
    """
    Recreate v_receive_weekly and v_receive_monthly VIEWs
    
    Pre-condition check:
    - Verifies mart.mv_receive_daily exists (dependency from 20251211_120000000)
    """
    print("[mart] Checking dependencies...")
    _check_mv_exists()
    
    print("[mart] Recreating v_receive_weekly...")
    op.execute(_read_sql("v_receive_weekly.sql"))
    
    print("[mart] Recreating v_receive_monthly...")
    op.execute(_read_sql("v_receive_monthly.sql"))
    
    print("[ok] v_receive_weekly and v_receive_monthly recreated")


def downgrade() -> None:
    """
    Drop v_receive_weekly and v_receive_monthly VIEWs
    """
    op.execute("DROP VIEW IF EXISTS mart.v_receive_monthly;")
    op.execute("DROP VIEW IF EXISTS mart.v_receive_weekly;")
