"""
ref schema tables: python baseline with safe guards

This migration creates 6 reference tables in the ref schema from the following DDL sources:
  - calendar_day.sql
  - calendar_exception.sql
  - calendar_month.sql
  - closure_membership.sql
  - closure_periods.sql
  - holiday_jp.sql

Each table creation is guarded with an existence check to ensure:
  - New/empty databases: tables are created normally
  - Existing databases: no changes occur (safe to stamp only)

Revision ID: 20251104_210000000
Revises: 20251104_164629413
Create Date: 2025-11-04 21:00:00.000000
"""

import sqlalchemy as sa
from alembic import context, op

# revision identifiers, used by Alembic.
revision = "20251104_210000000"
down_revision = "20251104_164629413"
branch_labels = None
depends_on = None


def _exists(qualified: str) -> bool:
    # オフライン(--sql)時はDBに問い合わせ不可。False固定でCREATEを出力させる。
    if context.is_offline_mode():
        return False
    conn = op.get_bind()
    return bool(
        conn.execute(
            sa.text("SELECT to_regclass(:q) IS NOT NULL"), {"q": qualified}
        ).scalar()
    )


def upgrade():
    """
    Create ref schema tables with existence guards.

    Order respects foreign key dependencies:
      1. calendar_day (no FK)
      2. closure_periods (no FK)
      3. holiday_jp (FK: calendar_day)
      4. calendar_month (no FK)
      5. calendar_exception (FK: calendar_day)
      6. closure_membership (FK: calendar_day, closure_periods)
    """
    # Ensure ref schema exists
    op.execute("CREATE SCHEMA IF NOT EXISTS ref;")

    # =========================================================================
    # 1. calendar_day
    # =========================================================================
    if not _exists("ref.calendar_day"):
        op.create_table(
            "calendar_day",
            sa.Column("ddate", sa.Date(), nullable=False),
            sa.Column(
                "y",
                sa.Integer(),
                sa.Computed("(EXTRACT(year FROM ddate))::integer", persisted=True),
                nullable=True,
            ),
            sa.Column(
                "m",
                sa.Integer(),
                sa.Computed("(EXTRACT(month FROM ddate))::integer", persisted=True),
                nullable=True,
            ),
            sa.Column(
                "iso_year",
                sa.Integer(),
                sa.Computed("(EXTRACT(isoyear FROM ddate))::integer", persisted=True),
                nullable=True,
            ),
            sa.Column(
                "iso_week",
                sa.Integer(),
                sa.Computed("(EXTRACT(week FROM ddate))::integer", persisted=True),
                nullable=True,
            ),
            sa.Column(
                "iso_dow",
                sa.Integer(),
                sa.Computed("(EXTRACT(isodow FROM ddate))::integer", persisted=True),
                nullable=True,
            ),
            sa.PrimaryKeyConstraint("ddate", name="calendar_day_pkey"),
            schema="ref",
        )

        # Indexes
        op.create_index(
            "ix_calendar_day_date",
            "calendar_day",
            ["ddate"],
            unique=False,
            schema="ref",
        )
        op.create_index(
            "ix_calendar_day_ym",
            "calendar_day",
            ["y", "m"],
            unique=False,
            schema="ref",
        )

    # =========================================================================
    # 2. closure_periods
    # =========================================================================
    if not _exists("ref.closure_periods"):
        op.create_table(
            "closure_periods",
            sa.Column("start_date", sa.Date(), nullable=False),
            sa.Column("end_date", sa.Date(), nullable=False),
            sa.Column("closure_name", sa.Text(), nullable=False),
            sa.CheckConstraint("start_date <= end_date", name="closure_periods_check"),
            sa.PrimaryKeyConstraint(
                "start_date", "end_date", name="closure_periods_pkey"
            ),
            schema="ref",
        )

    # =========================================================================
    # 3. holiday_jp
    # =========================================================================
    if not _exists("ref.holiday_jp"):
        op.create_table(
            "holiday_jp",
            sa.Column("hdate", sa.Date(), nullable=False),
            sa.Column("name", sa.Text(), nullable=False),
            sa.PrimaryKeyConstraint("hdate", name="holiday_jp_pkey"),
            sa.ForeignKeyConstraint(
                ["hdate"], ["ref.calendar_day.ddate"], name="fk_holiday_day"
            ),
            schema="ref",
        )

    # =========================================================================
    # 4. calendar_month
    # =========================================================================
    if not _exists("ref.calendar_month"):
        op.create_table(
            "calendar_month",
            sa.Column("month_date", sa.Date(), nullable=False),
            sa.PrimaryKeyConstraint("month_date", name="calendar_month_pkey"),
            schema="ref",
        )

    # =========================================================================
    # 5. calendar_exception
    # =========================================================================
    if not _exists("ref.calendar_exception"):
        op.create_table(
            "calendar_exception",
            sa.Column("ddate", sa.Date(), nullable=False),
            sa.Column("override_type", sa.Text(), nullable=False),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.Column("updated_by", sa.Text(), nullable=True),
            sa.Column(
                "updated_at",
                sa.TIMESTAMP(timezone=False),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.CheckConstraint(
                "override_type = ANY (ARRAY['FORCE_CLOSED'::text, 'FORCE_OPEN'::text, 'FORCE_RESERVATION'::text])",
                name="calendar_exception_override_type_check",
            ),
            sa.PrimaryKeyConstraint("ddate", name="calendar_exception_pkey"),
            sa.ForeignKeyConstraint(
                ["ddate"], ["ref.calendar_day.ddate"], name="fk_cal_exception_day"
            ),
            schema="ref",
        )

    # =========================================================================
    # 6. closure_membership
    # =========================================================================
    if not _exists("ref.closure_membership"):
        op.create_table(
            "closure_membership",
            sa.Column("ddate", sa.Date(), nullable=False),
            sa.Column("start_date", sa.Date(), nullable=False),
            sa.Column("end_date", sa.Date(), nullable=False),
            sa.Column("closure_name", sa.Text(), nullable=False),
            sa.PrimaryKeyConstraint("ddate", name="closure_membership_pkey"),
            sa.ForeignKeyConstraint(
                ["ddate"], ["ref.calendar_day.ddate"], name="fk_cm_day"
            ),
            sa.ForeignKeyConstraint(
                ["start_date", "end_date"],
                ["ref.closure_periods.start_date", "ref.closure_periods.end_date"],
                name="fk_cm_span",
            ),
            schema="ref",
        )


def downgrade():
    """
    Drop all ref schema tables in reverse order (respecting FK dependencies).
    """
    # Reverse order: tables with FK constraints first
    op.drop_table("closure_membership", schema="ref")
    op.drop_table("calendar_exception", schema="ref")
    op.drop_table("calendar_month", schema="ref")
    op.drop_table("holiday_jp", schema="ref")
    op.drop_table("closure_periods", schema="ref")

    # calendar_day: drop indexes then table
    op.drop_index("ix_calendar_day_ym", table_name="calendar_day", schema="ref")
    op.drop_index("ix_calendar_day_date", table_name="calendar_day", schema="ref")
    op.drop_table("calendar_day", schema="ref")
