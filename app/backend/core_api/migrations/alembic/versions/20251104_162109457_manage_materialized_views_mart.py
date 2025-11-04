"""manage materialized views: mart.*

Revision ID: 20251104_162109457
Revises: 20251104_160703155
Create Date: 2025-11-04 07:21:10.188840

"""
from alembic import op
import sqlalchemy as sa
from pathlib import Path


# revision identifiers, used by Alembic.
revision = '20251104_162109457'
down_revision = '20251104_160703155'
branch_labels = None
depends_on = None



BASE = Path("/backend/migrations/alembic/sql/mart")
def sql(name: str) -> str: return (BASE / name).read_text(encoding="utf-8")

def upgrade():
    # 依存の深い順に DROP（今回の4つは receive_daily に依存する側なので先に落としてOK）
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mart.mv_inb5y_week_profile_min CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mart.mv_inb_avg5y_day_biz CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mart.mv_inb_avg5y_weeksum_biz CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mart.mv_inb_avg5y_day_scope CASCADE;")

    # 再作成（ダンプした .sql には CREATE MATERIALIZED VIEW と CREATE UNIQUE INDEX が含まれている想定）
    op.execute(sql("mv_inb5y_week_profile_min.sql"))
    op.execute(sql("mv_inb_avg5y_day_biz.sql"))
    op.execute(sql("mv_inb_avg5y_weeksum_biz.sql"))
    op.execute(sql("mv_inb_avg5y_day_scope.sql"))

    # 初回リフレッシュが必要なら（重いので必要時のみ）
    # op.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mart.mv_inb_avg5y_day_scope;")

def downgrade():
    # 逆順でDROP（簡略運用）
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mart.mv_inb_avg5y_day_scope CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mart.mv_inb_avg5y_weeksum_biz CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mart.mv_inb_avg5y_day_biz CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mart.mv_inb5y_week_profile_min CASCADE;")