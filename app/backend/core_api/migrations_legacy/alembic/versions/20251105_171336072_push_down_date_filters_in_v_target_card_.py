"""push down date filters in v_target_card_per_day

Revision ID: 20251105_171336072
Revises: 20251105_170334790
Create Date: 2025-11-05 08:13:36.879301
"""
from alembic import op
import sqlalchemy as sa

revision = "20251105_171336072"
down_revision = "20251105_170334790"
branch_labels = None
depends_on = None

VIEW_SQL = """
CREATE OR REPLACE VIEW mart.v_target_card_per_day AS
WITH base AS (
  SELECT
    v.ddate,
    v.iso_year,
    v.iso_week,
    v.iso_dow,
    v.day_type,
    v.is_business,
    COALESCE(v.target_ton, 0)::numeric AS day_target_ton
  FROM mart.v_daily_target_with_calendar v
),
bounds AS (
  SELECT MIN(ddate) AS dmin, MAX(ddate) AS dmax FROM base
),
r AS (
  SELECT r.ddate, r.iso_year, r.iso_week, r.receive_net_ton
  FROM mart.v_receive_daily r, bounds
  WHERE r.ddate BETWEEN bounds.dmin - INTERVAL '1 day' AND bounds.dmax
),
week_target AS (
  SELECT
    v.iso_year,
    v.iso_week,
    SUM(COALESCE(v.target_ton, 0))::numeric AS week_target_ton
  FROM mart.v_daily_target_with_calendar v
  GROUP BY v.iso_year, v.iso_week
),
month_target AS (
  SELECT DISTINCT ON (date_trunc('month', mt.month_date)::date)
    date_trunc('month', mt.month_date)::date AS month_key,
    mt.value::numeric AS month_target_ton
  FROM kpi.monthly_targets mt
  WHERE mt.metric = 'inbound' AND mt.segment = 'factory'
  ORDER BY date_trunc('month', mt.month_date)::date, mt.updated_at DESC
),
week_actual AS (
  SELECT r.iso_year, r.iso_week, SUM(COALESCE(r.receive_net_ton, 0)) AS week_actual_ton
  FROM r
  GROUP BY r.iso_year, r.iso_week
),
month_actual AS (
  SELECT date_trunc('month', r.ddate)::date AS month_key,
         SUM(COALESCE(r.receive_net_ton, 0)) AS month_actual_ton
  FROM r
  GROUP BY date_trunc('month', r.ddate)::date
)
SELECT
  b.ddate,
  b.day_target_ton,
  wt.week_target_ton,
  mt.month_target_ton,
  COALESCE(rprev.receive_net_ton, 0)::numeric AS day_actual_ton_prev,
  COALESCE(wa.week_actual_ton, 0)::numeric AS week_actual_ton,
  COALESCE(ma.month_actual_ton, 0)::numeric AS month_actual_ton,
  b.iso_year,
  b.iso_week,
  b.iso_dow,
  b.day_type,
  b.is_business
FROM base b
LEFT JOIN week_target wt
  ON wt.iso_year = b.iso_year AND wt.iso_week = b.iso_week
LEFT JOIN month_target mt
  ON mt.month_key = date_trunc('month', b.ddate)::date
LEFT JOIN week_actual wa
  ON wa.iso_year = b.iso_year AND wa.iso_week = b.iso_week
LEFT JOIN month_actual ma
  ON ma.month_key = date_trunc('month', b.ddate)::date
LEFT JOIN r rprev
  ON rprev.ddate = b.ddate - INTERVAL '1 day'
ORDER BY b.ddate;
"""

def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(sa.text(VIEW_SQL))

def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(sa.text(
            "DO $$ BEGIN RAISE NOTICE 'no-op downgrade for %', :rev; END $$;"
        ), {"rev": revision})
