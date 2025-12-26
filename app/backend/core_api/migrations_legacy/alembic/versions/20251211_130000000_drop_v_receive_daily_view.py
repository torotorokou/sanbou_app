"""drop v_receive_daily view - replaced by mv_receive_daily

Purpose:
  Drop the obsolete mart.v_receive_daily VIEW after migration to
  mart.mv_receive_daily materialized view is complete.

Context:
  - mv_receive_daily was created in migration 20251211_120000000
  - All dependent objects (MVs and VIEWs) now reference mv_receive_daily
  - sql_names.py constant V_RECEIVE_DAILY updated to point to mv_receive_daily

Cascade Effects:
  - DROP VIEW ... CASCADE will drop dependent objects
  - v_receive_weekly and v_receive_monthly were dropped and recreated
  - 5-year average MVs were dropped and recreated

Revision ID: 20251211_130000000
Revises: 20251211_120000000
Create Date: 2025-12-11 13:00:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251211_130000000"
down_revision = "20251211_120000000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Drop v_receive_daily VIEW (replaced by mv_receive_daily materialized view)

    Note: CASCADE will drop dependent objects:
    - mart.v_receive_weekly
    - mart.v_receive_monthly
    - mart.mv_inb5y_week_profile_min
    - mart.mv_inb_avg5y_day_biz
    - mart.mv_inb_avg5y_weeksum_biz
    - mart.mv_inb_avg5y_day_scope

    These will be recreated in subsequent migrations.
    """
    op.execute("DROP VIEW IF EXISTS mart.v_receive_daily CASCADE;")


def downgrade() -> None:
    """
    Recreate v_receive_daily VIEW as a wrapper to mv_receive_daily

    Note: This is for migration reversibility only.
    In practice, we don't want to restore the old VIEW.
    """
    op.execute(
        """
        CREATE OR REPLACE VIEW mart.v_receive_daily AS
        SELECT * FROM mart.mv_receive_daily;
    """
    )
