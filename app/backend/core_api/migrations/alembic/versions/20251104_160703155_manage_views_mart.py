"""manage views: mart.*

Revision ID: 20251104_160703155
Revises: 20251104_154033124
Create Date: 2025-11-04 07:07:03.956955

"""
from alembic import op
import sqlalchemy as sa
from pathlib import Path


# revision identifiers, used by Alembic.
revision = '20251104_160703155'
down_revision = '20251104_154033124'
branch_labels = None
depends_on = None



BASE = Path("/backend/migrations/alembic/sql/mart")
def _sql(name: str) -> str: return (BASE / name).read_text(encoding="utf-8")

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
        ("stg", "receive_shogun_final"),
        ("stg", "receive_shogun_flash"),
        ("stg", "receive_king_final"),
    ]
    
    all_tables_exist = all(_table_exists(schema, table) for schema, table in required_tables)
    
    if not all_tables_exist:
        print("⚠️  Skipping view creation - required stg tables do not exist yet")
        print("   Views will be created by later migrations")
        return
    
    op.execute(_sql("receive_daily.sql"))
    op.execute(_sql("receive_weekly.sql"))
    op.execute(_sql("receive_monthly.sql"))
    op.execute(_sql("v_daily_target_with_calendar.sql"))
    op.execute(_sql("v_target_card_per_day.sql"))

def downgrade():
    pass  # ここは空でOK（必要なら後で整備）