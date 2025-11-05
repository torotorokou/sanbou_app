"""manage view: mart.v_target_card_per_day

Revision ID: d64c705dde4a
Revises: 83f7cf7d956e
Create Date: 2025-11-04
"""
from alembic import op
from textwrap import dedent

# revision identifiers, used by Alembic.
revision = "d64c705dde4a"
down_revision = "83f7cf7d956e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 依存: mart.v_daily_target_with_calendar, kpi.monthly_targets, mart.receive_daily
    op.execute(
        dedent(
            """
            CREATE OR REPLACE VIEW mart.v_target_card_per_day AS
            WITH base AS (
                SELECT
                    v.ddate,
                    v.iso_year,
                    v.iso_week,
                    v.iso_dow,
                    v.day_type,
                    v.is_business,
                    COALESCE(v.target_ton, 0::double precision)::numeric AS day_target_ton
                FROM mart.v_daily_target_with_calendar v
            ),
            week_target AS (
                SELECT
                    v_daily_target_with_calendar.iso_year,
                    v_daily_target_with_calendar.iso_week,
                    SUM(COALESCE(v_daily_target_with_calendar.target_ton, 0::double precision))::numeric AS week_target_ton
                FROM mart.v_daily_target_with_calendar
                GROUP BY v_daily_target_with_calendar.iso_year, v_daily_target_with_calendar.iso_week
            ),
            month_target AS (
                SELECT DISTINCT ON ((date_trunc('month', mt_1.month_date::timestamptz)::date))
                    date_trunc('month', mt_1.month_date::timestamptz)::date AS month_key,
                    mt_1.value::numeric AS month_target_ton
                FROM kpi.monthly_targets mt_1
                WHERE mt_1.metric = 'inbound' AND mt_1.segment = 'factory'
                ORDER BY (date_trunc('month', mt_1.month_date::timestamptz)::date), mt_1.updated_at DESC
            ),
            week_actual AS (
                SELECT
                    r.iso_year,
                    r.iso_week,
                    SUM(COALESCE(r.receive_net_ton, 0::numeric)) AS week_actual_ton
                FROM mart.receive_daily r
                GROUP BY r.iso_year, r.iso_week
            ),
            month_actual AS (
                SELECT
                    date_trunc('month', r.ddate::timestamptz)::date AS month_key,
                    SUM(COALESCE(r.receive_net_ton, 0::numeric)) AS month_actual_ton
                FROM mart.receive_daily r
                GROUP BY (date_trunc('month', r.ddate::timestamptz)::date)
            )
            SELECT
                b.ddate,
                b.day_target_ton,
                wt.week_target_ton,
                mt.month_target_ton,
                COALESCE(rprev.receive_net_ton, 0::numeric) AS day_actual_ton_prev,
                COALESCE(wa.week_actual_ton, 0::numeric) AS week_actual_ton,
                COALESCE(ma.month_actual_ton, 0::numeric) AS month_actual_ton,
                b.iso_year,
                b.iso_week,
                b.iso_dow,
                b.day_type,
                b.is_business
            FROM base b
            LEFT JOIN week_target wt
              ON wt.iso_year = b.iso_year AND wt.iso_week = b.iso_week
            LEFT JOIN month_target mt
              ON mt.month_key = date_trunc('month', b.ddate::timestamptz)::date
            LEFT JOIN week_actual wa
              ON wa.iso_year = b.iso_year AND wa.iso_week = b.iso_week
            LEFT JOIN month_actual ma
              ON ma.month_key = date_trunc('month', b.ddate::timestamptz)::date
            LEFT JOIN mart.receive_daily rprev
              ON rprev.ddate = (b.ddate - INTERVAL '1 day')
            ORDER BY b.ddate;
            """
        )
    )


def downgrade() -> None:
    # 依存オブジェクトがある場合はDROPが失敗することがあります。
    # 可逆にしたい場合は、直前版のCREATE OR REPLACE VIEWをここに記載してください。
    op.execute("DROP VIEW IF EXISTS mart.v_target_card_per_day;")
