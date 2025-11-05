"""mart: canonicalize receive_* into v_receive_* and keep wrappers

Revision ID: 20251105_100819527
Revises: 20251105_091950593
Create Date: 2025-11-05 01:08:20.295566

"""
from alembic import op
import sqlalchemy as sa
from pathlib import Path


# revision identifiers, used by Alembic.
revision = '20251105_100819527'
down_revision = '20251105_091950593'
branch_labels = None
depends_on = None

SQL_BASE = Path("/backend/migrations/alembic/sql/mart")

def _run(name: str) -> None:
    op.execute((SQL_BASE / name).read_text())

def upgrade():
    # 1) 正史を v_* 側に配置
    _run("v_receive_daily.sql")
    _run("v_receive_weekly.sql")
    _run("v_receive_monthly.sql")

    # 2) 旧名は互換ラッパー（パススルー）
    op.execute("CREATE OR REPLACE VIEW mart.receive_daily   AS SELECT * FROM mart.v_receive_daily;")
    op.execute("CREATE OR REPLACE VIEW mart.receive_weekly  AS SELECT * FROM mart.v_receive_weekly;")
    op.execute("CREATE OR REPLACE VIEW mart.receive_monthly AS SELECT * FROM mart.v_receive_monthly;")

def downgrade():
    # 非破壊ポリシーのため DROP はしない
    pass