"""manage views: ref.*

Revision ID: 20251104_163649629
Revises: 20251104_162109457
Create Date: 2025-11-04 07:36:50.366895

"""
from alembic import op
import sqlalchemy as sa
from pathlib import Path


# revision identifiers, used by Alembic.
revision = '20251104_163649629'
down_revision = '20251104_162109457'
branch_labels = None
depends_on = None

# コンテナ内の .sql 置き場
BASE = Path("/backend/migrations/alembic/sql/ref")

def _read_sql(fname: str) -> str:
    return (BASE / fname).read_text(encoding="utf-8")

def _table_exists(schema: str, table: str) -> bool:
    """Check if a table exists"""
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT to_regclass(:qualified) IS NOT NULL"),
        {"qualified": f"{schema}.{table}"}
    ).scalar()
    return bool(result)

def upgrade():
    # Check if required tables exist before creating views
    required_tables = [
        ("ref", "calendar_day"),
        ("ref", "holiday_jp"),
    ]
    
    all_tables_exist = all(_table_exists(schema, table) for schema, table in required_tables)
    
    if not all_tables_exist:
        print("⚠️  Skipping ref view creation - required ref tables do not exist yet")
        print("   Views will be created by later migrations")
        return
    
    # 依存の浅い順に実行したい場合は明示順で。
    # 今回はどちらもテーブル参照のみなので順不同でもOK。
    for fname in sorted(p.name for p in BASE.glob("*.sql")):
        op.execute(_read_sql(fname))

def downgrade():
    # 必要ならDROPを書く（簡易運用なら空で可）
    # op.execute("DROP VIEW IF EXISTS ref.v_closure_days")
    # op.execute("DROP VIEW IF EXISTS ref.v_calendar_classified")
    pass