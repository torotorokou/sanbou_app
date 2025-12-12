-- inbound_pg_repository__get_daily_with_comparisons.sql
-- Fetch daily inbound data with cumulative sums AND comparison data (prev month / prev year)
--
-- Parameters:
--   :start - Start date (inclusive)
--   :end - End date (inclusive)
--   :cum_scope - Cumulative scope: 'range', 'month', 'week', or 'none'
--
-- Comparison Logic:
--   - prev_month: Same day 4 weeks ago (28 days)
--   - prev_year: Same ISO week + ISO day-of-week in previous year

WITH d AS (
  -- Base CTE: Target period data with calendar continuity
  SELECT
    c.ddate,
    c.iso_year,
    c.iso_week,
    c.iso_dow,
    c.is_business,
    COALESCE(r.receive_net_ton, 0)::numeric AS ton
  FROM {v_calendar} AS c
  LEFT JOIN {mv_receive_daily} AS r
    ON r.ddate = c.ddate
  WHERE c.ddate BETWEEN :start AND :end
),
prev_month AS (
  -- Previous month comparison: 4 weeks ago (28 days)
  SELECT
    c.ddate + INTERVAL '28 days' AS target_ddate,
    COALESCE(r.receive_net_ton, 0)::numeric AS pm_ton
  FROM {v_calendar} AS c
  LEFT JOIN {mv_receive_daily} AS r
    ON r.ddate = c.ddate
  WHERE c.ddate BETWEEN (:start - INTERVAL '28 days') AND (:end - INTERVAL '28 days')
),
prev_year AS (
  -- Previous year comparison: Same ISO week + ISO day-of-week in previous year
  SELECT
    c_curr.ddate AS target_ddate,
    COALESCE(r_prev.receive_net_ton, 0)::numeric AS py_ton
  FROM {v_calendar} AS c_curr
  LEFT JOIN {v_calendar} AS c_prev
    ON c_prev.iso_year = c_curr.iso_year - 1
    AND c_prev.iso_week = c_curr.iso_week
    AND c_prev.iso_dow = c_curr.iso_dow
  LEFT JOIN {mv_receive_daily} AS r_prev
    ON r_prev.ddate = c_prev.ddate
  WHERE c_curr.ddate BETWEEN :start AND :end
),
base_with_comparisons AS (
  -- Join base data with comparison data
  SELECT
    d.ddate,
    d.iso_year,
    d.iso_week,
    d.iso_dow,
    d.is_business,
    d.ton,
    COALESCE(pm.pm_ton, 0)::numeric AS prev_month_ton,
    COALESCE(py.py_ton, 0)::numeric AS prev_year_ton
  FROM d
  LEFT JOIN prev_month pm ON pm.target_ddate = d.ddate
  LEFT JOIN prev_year py ON py.target_ddate = d.ddate
)
SELECT
  b.ddate,
  b.iso_year,
  b.iso_week,
  b.iso_dow,
  b.is_business,
  NULL::text AS segment,  -- Reserved for future segment support
  b.ton,
  -- Current period cumulative
  CASE
    WHEN :cum_scope = 'range' THEN
      SUM(b.ton) OVER (
        ORDER BY b.ddate
        ROWS UNBOUNDED PRECEDING
      )
    WHEN :cum_scope = 'month' THEN
      SUM(b.ton) OVER (
        PARTITION BY DATE_TRUNC('month', b.ddate)
        ORDER BY b.ddate
        ROWS UNBOUNDED PRECEDING
      )
    WHEN :cum_scope = 'week' THEN
      SUM(b.ton) OVER (
        PARTITION BY b.iso_year, b.iso_week
        ORDER BY b.ddate
        ROWS UNBOUNDED PRECEDING
      )
    ELSE NULL
  END AS cum_ton,
  -- Comparison: Previous month (4 weeks ago)
  b.prev_month_ton,
  -- Comparison: Previous year (same ISO week/dow)
  b.prev_year_ton,
  -- Cumulative comparison: Previous month
  CASE
    WHEN :cum_scope = 'range' THEN
      SUM(b.prev_month_ton) OVER (
        ORDER BY b.ddate
        ROWS UNBOUNDED PRECEDING
      )
    WHEN :cum_scope = 'month' THEN
      SUM(b.prev_month_ton) OVER (
        PARTITION BY DATE_TRUNC('month', b.ddate)
        ORDER BY b.ddate
        ROWS UNBOUNDED PRECEDING
      )
    WHEN :cum_scope = 'week' THEN
      SUM(b.prev_month_ton) OVER (
        PARTITION BY b.iso_year, b.iso_week
        ORDER BY b.ddate
        ROWS UNBOUNDED PRECEDING
      )
    ELSE NULL
  END AS prev_month_cum_ton,
  -- Cumulative comparison: Previous year
  CASE
    WHEN :cum_scope = 'range' THEN
      SUM(b.prev_year_ton) OVER (
        ORDER BY b.ddate
        ROWS UNBOUNDED PRECEDING
      )
    WHEN :cum_scope = 'month' THEN
      SUM(b.prev_year_ton) OVER (
        PARTITION BY DATE_TRUNC('month', b.ddate)
        ORDER BY b.ddate
        ROWS UNBOUNDED PRECEDING
      )
    WHEN :cum_scope = 'week' THEN
      SUM(b.prev_year_ton) OVER (
        PARTITION BY b.iso_year, b.iso_week
        ORDER BY b.ddate
        ROWS UNBOUNDED PRECEDING
      )
    ELSE NULL
  END AS prev_year_cum_ton
FROM base_with_comparisons b
ORDER BY b.ddate
