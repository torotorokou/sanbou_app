"""ref_baseline_tables

Revision ID: 20251104_164629413
Revises: 20251104_163649629
Create Date: 2025-11-04 07:46:30.159549

"""
from alembic import op
import sqlalchemy as sa
from pathlib import Path


# revision identifiers, used by Alembic.
revision = '20251104_164629413'
down_revision = '20251104_163649629'
branch_labels = None
depends_on = None

# コンテナ内パスで参照
TABLES_DIR = Path("/backend/migrations/alembic/sql/ref/tables")

def _read_sql(name: str) -> str:
    return (TABLES_DIR / name).read_text(encoding="utf-8")

def upgrade() -> None:
    # 念のため（存在してもOK）
    op.execute("CREATE SCHEMA IF NOT EXISTS ref;")

    # 参照関係に配慮して作成順を固定
    # 1) 参照される側 → 2) 参照する側
    op.execute(_read_sql("calendar_day.sql"))
    op.execute(_read_sql("closure_periods.sql"))
    op.execute(_read_sql("holiday_jp.sql"))
    op.execute(_read_sql("calendar_month.sql"))
    op.execute(_read_sql("calendar_exception.sql"))   # FK: calendar_day
    op.execute(_read_sql("closure_membership.sql"))   # FK: calendar_day, closure_periods

def downgrade() -> None:
    # 参照する側から順にDROP
    op.execute("DROP TABLE IF EXISTS ref.closure_membership CASCADE;")
    op.execute("DROP TABLE IF EXISTS ref.calendar_exception CASCADE;")
    op.execute("DROP TABLE IF EXISTS ref.calendar_month CASCADE;")
    op.execute("DROP TABLE IF EXISTS ref.holiday_jp CASCADE;")
    op.execute("DROP TABLE IF EXISTS ref.closure_periods CASCADE;")
    op.execute("DROP TABLE IF EXISTS ref.calendar_day CASCADE;")