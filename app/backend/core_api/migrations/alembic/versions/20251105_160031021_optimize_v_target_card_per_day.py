"""optimize v_target_card_per_day

Revision ID: 20251105_160031021
Revises: 20251105_153337731
Create Date: 2025-11-05 07:00:31.827595

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251105_160031021'
down_revision = '20251105_153337731'
branch_labels = None
depends_on = None

def upgrade():
    # 最適化版：v_receive_daily を1回だけ評価 + base範囲に限定
    op.execute("""
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
    base_range AS (
        SELECT MIN(ddate) AS dmin, MAX(ddate) AS dmax
        FROM base
    ),
    r AS (
        -- v_receive_daily を一度だけ取り出し、前日参照のため dmin-1日 も含める
        SELECT r0.*
        FROM mart.v_receive_daily r0, base_range br
        WHERE r0.ddate BETWEEN (br.dmin - INTERVAL '1 day') AND br.dmax
    ),
    week_target AS (
        SELECT
            v.iso_year,
            v.iso_week,
            SUM(COALESCE(v.target_ton, 0::double precision))::numeric AS week_target_ton
        FROM mart.v_daily_target_with_calendar v
        GROUP BY v.iso_year, v.iso_week
    ),
    month_target AS (
        SELECT DISTINCT ON (date_trunc('month', mt.month_date::timestamptz)::date)
            date_trunc('month', mt.month_date::timestamptz)::date AS month_key,
            mt.value::numeric AS month_target_ton
        FROM kpi.monthly_targets mt
        WHERE mt.metric = 'inbound' AND mt.segment = 'factory'
        ORDER BY date_trunc('month', mt.month_date::timestamptz)::date, mt.updated_at DESC
    ),
    week_actual AS (
        SELECT
            r.iso_year,
            r.iso_week,
            SUM(COALESCE(r.receive_net_ton, 0::numeric)) AS week_actual_ton
        FROM r
        GROUP BY r.iso_year, r.iso_week
    ),
    month_actual AS (
        SELECT
            date_trunc('month', r.ddate::timestamptz)::date AS month_key,
            SUM(COALESCE(r.receive_net_ton, 0::numeric)) AS month_actual_ton
        FROM r
        GROUP BY date_trunc('month', r.ddate::timestamptz)::date
    )
    SELECT
        b.ddate,
        b.day_target_ton,
        wt.week_target_ton,
        mt.month_target_ton,
        COALESCE(rprev.receive_net_ton, 0::numeric) AS day_actual_ton_prev,
        COALESCE(wa.week_actual_ton, 0::numeric)     AS week_actual_ton,
        COALESCE(ma.month_actual_ton, 0::numeric)    AS month_actual_ton,
        b.iso_year,
        b.iso_week,
        b.iso_dow,
        b.day_type,
        b.is_business
    FROM base b
    LEFT JOIN week_target  wt
           ON wt.iso_year = b.iso_year AND wt.iso_week = b.iso_week
    LEFT JOIN month_target mt
           ON mt.month_key = date_trunc('month', b.ddate::timestamptz)::date
    LEFT JOIN week_actual  wa
           ON wa.iso_year = b.iso_year AND wa.iso_week = b.iso_week
    LEFT JOIN month_actual ma
           ON ma.month_key = date_trunc('month', b.ddate::timestamptz)::date
    LEFT JOIN r rprev
           ON rprev.ddate = (b.ddate - INTERVAL '1 day')
    ORDER BY b.ddate;
    """)

    # （任意）基礎テーブルにインデックスを用意。存在すればスキップされます。
    # スキーマ名・テーブル名は実データに合わせてください。
    op.execute("""
    DO $$
    BEGIN
        IF to_regclass('mart.receive_daily') IS NOT NULL THEN
            EXECUTE 'CREATE INDEX IF NOT EXISTS idx_receive_daily_ddate ON mart.receive_daily (ddate)';
            EXECUTE 'CREATE INDEX IF NOT EXISTS idx_receive_daily_iso_year_week ON mart.receive_daily (iso_year, iso_week)';
        END IF;
        IF to_regclass('mart.receive_king_final') IS NOT NULL THEN
            EXECUTE 'CREATE INDEX IF NOT EXISTS idx_king_invoice_date_date ON mart.receive_king_final ((invoice_date::date))';
        END IF;
    END$$;
    """)


def downgrade():
    # 元の定義（あなたが提示したDDL）に戻します
    op.execute("""
    CREATE OR REPLACE VIEW mart.v_target_card_per_day
    AS WITH base AS (
             SELECT v.ddate,
                v.iso_year,
                v.iso_week,
                v.iso_dow,
                v.day_type,
                v.is_business,
                COALESCE(v.target_ton, 0::double precision)::numeric AS day_target_ton
               FROM mart.v_daily_target_with_calendar v
            ), week_target AS (
             SELECT v_daily_target_with_calendar.iso_year,
                v_daily_target_with_calendar.iso_week,
                sum(COALESCE(v_daily_target_with_calendar.target_ton, 0::double precision))::numeric AS week_target_ton
               FROM mart.v_daily_target_with_calendar
              GROUP BY v_daily_target_with_calendar.iso_year, v_daily_target_with_calendar.iso_week
            ), month_target AS (
             SELECT DISTINCT ON ((date_trunc('month'::text, mt_1.month_date::timestamp with time zone)::date)) date_trunc('month'::text, mt_1.month_date::timestamp with time zone)::date AS month_key,
                mt_1.value::numeric AS month_target_ton
               FROM kpi.monthly_targets mt_1
              WHERE mt_1.metric = 'inbound'::text AND mt_1.segment = 'factory'::text
              ORDER BY (date_trunc('month'::text, mt_1.month_date::timestamp with time zone)::date), mt_1.updated_at DESC
            ), week_actual AS (
             SELECT r.iso_year,
                r.iso_week,
                sum(COALESCE(r.receive_net_ton, 0::numeric)) AS week_actual_ton
               FROM mart.v_receive_daily r
              GROUP BY r.iso_year, r.iso_week
            ), month_actual AS (
             SELECT date_trunc('month'::text, r.ddate::timestamp with time zone)::date AS month_key,
                sum(COALESCE(r.receive_net_ton, 0::numeric)) AS month_actual_ton
               FROM mart.v_receive_daily r
              GROUP BY (date_trunc('month'::text, r.ddate::timestamp with time zone)::date)
            )
     SELECT b.ddate,
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
         LEFT JOIN week_target wt ON wt.iso_year = b.iso_year AND wt.iso_week = b.iso_week
         LEFT JOIN month_target mt ON mt.month_key = date_trunc('month'::text, b.ddate::timestamp with time zone)::date
         LEFT JOIN week_actual wa ON wa.iso_year = b.iso_year AND wa.iso_week = b.iso_week
         LEFT JOIN month_actual ma ON ma.month_key = date_trunc('month'::text, b.ddate::timestamp with time zone)::date
         LEFT JOIN mart.v_receive_daily rprev ON rprev.ddate = (b.ddate - '1 day'::interval)
      ORDER BY b.ddate;
    """)