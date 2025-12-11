"""recreate 5-year average materialized views

Purpose:
  Recreate the 5-year inbound average materialized views that were
  dropped due to CASCADE when dropping mart.v_receive_daily.

Context:
  - These MVs now reference mart.mv_receive_daily instead of v_receive_daily
  - SQL definitions updated in sql/mart/mv_inb*.sql files
  - Used for forecasting and historical trend analysis

MVs recreated:
  - mv_inb5y_week_profile_min: 5-year weekly profile (weekday vs holiday averages)
  - mv_inb_avg5y_day_biz: 5-year business day averages by ISO week and day
  - mv_inb_avg5y_weeksum_biz: 5-year weekly sum averages (business days only)
  - mv_inb_avg5y_day_scope: 5-year daily averages with scope (all/biz)

Dependencies:
  - Requires mart.mv_receive_daily to exist (created in 20251211_120000000)

Revision ID: 20251211_150000000
Revises: 20251211_140000000
Create Date: 2025-12-11 15:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from pathlib import Path


# revision identifiers, used by Alembic.
revision = '20251211_150000000'
down_revision = '20251211_140000000'
branch_labels = None
depends_on = None


BASE = Path("/backend/migrations/alembic/sql/mart")


def _read_sql(name: str) -> str:
    """Read SQL file content"""
    p = BASE / name
    with open(p, "r", encoding="utf-8") as f:
        return f.read()


def upgrade() -> None:
    """
    Recreate 5-year average materialized views with UNIQUE indexes
    """
    # 1. mv_inb5y_week_profile_min
    print("[mart] Recreating mv_inb5y_week_profile_min...")
    op.execute(_read_sql("mv_inb5y_week_profile_min.sql"))
    op.execute("""
        CREATE UNIQUE INDEX mv_inb5y_week_profile_min_pk 
        ON mart.mv_inb5y_week_profile_min (iso_week);
    """)
    op.execute("REFRESH MATERIALIZED VIEW mart.mv_inb5y_week_profile_min;")
    
    # 2. mv_inb_avg5y_day_biz
    print("[mart] Recreating mv_inb_avg5y_day_biz...")
    op.execute(_read_sql("mv_inb_avg5y_day_biz.sql"))
    op.execute("""
        CREATE UNIQUE INDEX mv_inb_avg5y_day_biz_pk 
        ON mart.mv_inb_avg5y_day_biz (iso_week, iso_dow);
    """)
    op.execute("REFRESH MATERIALIZED VIEW mart.mv_inb_avg5y_day_biz;")
    
    # 3. mv_inb_avg5y_weeksum_biz
    print("[mart] Recreating mv_inb_avg5y_weeksum_biz...")
    op.execute(_read_sql("mv_inb_avg5y_weeksum_biz.sql"))
    op.execute("""
        CREATE UNIQUE INDEX mv_inb_avg5y_weeksum_biz_pk 
        ON mart.mv_inb_avg5y_weeksum_biz (iso_week);
    """)
    op.execute("REFRESH MATERIALIZED VIEW mart.mv_inb_avg5y_weeksum_biz;")
    
    # 4. mv_inb_avg5y_day_scope
    print("[mart] Recreating mv_inb_avg5y_day_scope...")
    op.execute(_read_sql("mv_inb_avg5y_day_scope.sql"))
    op.execute("""
        CREATE UNIQUE INDEX ux_mv_inb_avg5y_day_scope 
        ON mart.mv_inb_avg5y_day_scope (scope, iso_week, iso_dow);
    """)
    op.execute("REFRESH MATERIALIZED VIEW mart.mv_inb_avg5y_day_scope;")
    
    print("[ok] All 5-year average MVs recreated and refreshed")


def downgrade() -> None:
    """
    Drop 5-year average materialized views
    """
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mart.mv_inb_avg5y_day_scope;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mart.mv_inb_avg5y_weeksum_biz;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mart.mv_inb_avg5y_day_biz;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mart.mv_inb5y_week_profile_min;")
