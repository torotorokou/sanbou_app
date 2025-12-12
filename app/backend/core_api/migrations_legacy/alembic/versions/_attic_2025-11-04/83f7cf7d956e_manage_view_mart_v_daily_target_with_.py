"""manage view: mart.v_daily_target_with_calendar

Revision ID: 83f7cf7d956e
Revises: 9a092c4a1fcf
Create Date: 2025-11-04 04:58:18.783472
"""
from alembic import op
import sqlalchemy as sa  # noqa: F401
from textwrap import dedent


# revision identifiers, used by Alembic.
revision = "83f7cf7d956e"
down_revision = "9a092c4a1fcf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 依存: ref.v_calendar_classified, mart.daily_target_plan
    op.execute(
        dedent(
            """
            CREATE OR REPLACE VIEW mart.v_daily_target_with_calendar AS
            SELECT
              c.ddate,
              c.iso_year,
              c.iso_week,
              c.iso_dow,
              c.day_type,
              c.is_business,
              p.target_ton,
              p.scope_used,
              p.created_at
            FROM ref.v_calendar_classified AS c
            LEFT JOIN mart.daily_target_plan AS p
              ON c.ddate = p.ddate;
            """
        )
    )


def downgrade() -> None:
    # 初回取り込みのため、元の定義が不明なケースを想定して安全にDROPのみ
    # （将来“前の定義”に戻したい場合は、ここに以前のCREATE OR REPLACE VIEWを記述してください）
    op.execute("DROP VIEW IF EXISTS mart.v_daily_target_with_calendar;")
