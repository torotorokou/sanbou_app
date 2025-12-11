-- Simplified daily inbound query (Proposal #6)
-- No prev_month/prev_year comparisons, only current period + cumulative calculations
-- Expected impact: 20-30% faster than get_daily_with_comparisons

WITH d AS (
  -- Base CTE: Target period data with calendar continuity
  SELECT
    c.ddate,
    c.iso_year,
    c.iso_week,
    c.iso_dow,
    c.is_business,
    COALESCE(r.receive_net_ton, 0)::numeric AS ton
  FROM mart.v_calendar AS c
  LEFT JOIN mart.mv_receive_daily AS r
    ON r.ddate = c.ddate
  WHERE c.ddate BETWEEN :start AND :end
),
weekly_agg AS (
  -- Weekly aggregation for current period
  SELECT
    iso_year,
    iso_week,
    SUM(ton) AS week_ton
  FROM d
  WHERE is_business
  GROUP BY iso_year, iso_week
)
SELECT
  d.ddate,
  d.iso_year,
  d.iso_week,
  d.iso_dow,
  d.is_business,
  d.ton AS day_ton,
  wa.week_ton,
  -- Month cumulative (from start of month to current date)
  SUM(d.ton) FILTER (WHERE d.is_business)
    OVER (ORDER BY d.ddate ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS month_cumulative_ton,
  -- Week cumulative (within same iso_week)
  SUM(d.ton) FILTER (WHERE d.is_business)
    OVER (PARTITION BY d.iso_year, d.iso_week ORDER BY d.ddate) AS week_cumulative_ton
FROM d
LEFT JOIN weekly_agg AS wa
  ON wa.iso_year = d.iso_year AND wa.iso_week = d.iso_week
ORDER BY d.ddate;
