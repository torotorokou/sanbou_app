"""mart: mark receive_* wrappers as deprecated

Revision ID: 20251105_101107506
Revises: 20251105_100819527
Create Date: 2025-11-05 01:11:08.349847

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251105_101107506'
down_revision = '20251105_100819527'
branch_labels = None
depends_on = None



def upgrade():
    op.execute("COMMENT ON VIEW mart.receive_daily   IS 'DEPRECATED: use mart.v_receive_daily';")
    op.execute("COMMENT ON VIEW mart.receive_weekly  IS 'DEPRECATED: use mart.v_receive_weekly';")
    op.execute("COMMENT ON VIEW mart.receive_monthly IS 'DEPRECATED: use mart.v_receive_monthly';")

def downgrade():
    # 非破壊主義：戻す必要なし
    pass