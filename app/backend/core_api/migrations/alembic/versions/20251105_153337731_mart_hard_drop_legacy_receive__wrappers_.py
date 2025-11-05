"""mart: hard-drop legacy receive_* wrappers (finalize)

Revision ID: 20251105_153337731
Revises: 20251105_152407663
Create Date: 2025-11-05 06:33:38.491175

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251105_153337731'
down_revision = '20251105_152407663'
branch_labels = None
depends_on = None


def upgrade():
    # 既にDROP済みでもOK（IF EXISTS）
    op.execute("DROP VIEW IF EXISTS mart.receive_daily;")
    op.execute("DROP VIEW IF EXISTS mart.receive_weekly;")
    op.execute("DROP VIEW IF EXISTS mart.receive_monthly;")

def downgrade():
    # 互換レイヤ（必要になったら復活できる）
    op.execute("CREATE OR REPLACE VIEW mart.receive_daily   AS SELECT * FROM mart.v_receive_daily;")
    op.execute("CREATE OR REPLACE VIEW mart.receive_weekly  AS SELECT * FROM mart.v_receive_weekly;")
    op.execute("CREATE OR REPLACE VIEW mart.receive_monthly AS SELECT * FROM mart.v_receive_monthly;")