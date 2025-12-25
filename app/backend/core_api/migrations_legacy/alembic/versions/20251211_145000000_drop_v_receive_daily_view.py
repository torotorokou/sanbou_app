"""drop v_receive_daily view

Revision ID: 20251211_145000000
Revises: 20251211_120000000
Create Date: 2025-12-11 14:50:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20251211_145000000"
down_revision = "20251211_120000000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop v_receive_daily VIEW (replaced by mv_receive_daily materialized view)
    op.execute("DROP VIEW IF EXISTS mart.v_receive_daily CASCADE;")


def downgrade() -> None:
    # Recreate v_receive_daily VIEW from mv_receive_daily definition
    # Note: In practice, we don't want to restore the old VIEW
    # This is here for migration reversibility only
    op.execute(
        """
        CREATE OR REPLACE VIEW mart.v_receive_daily AS
        SELECT * FROM mart.mv_receive_daily;
    """
    )
