-- inbound_pg_repository__get_daily_with_cumulative.sql
-- Fetch daily inbound data with cumulative sums using window functions
--
-- Parameters:
--   :start - Start date (inclusive)
--   :end - End date (inclusive)
--   :cum_scope - Cumulative scope: 'range', 'month', or 'week'
--
-- Note:
--   - segment filtering is not yet supported (reserved for future)
--   - Calendar data is LEFT JOINed with receive data

WITH d AS (
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
)
SELECT
  d.ddate,
  d.iso_year,
  d.iso_week,
  d.iso_dow,
  d.is_business,
  NULL::text AS segment,  -- 互換のため形だけ返す（将来segment対応時に置換）
  d.ton,
  CASE
    WHEN :cum_scope = 'range' THEN
      SUM(d.ton) OVER (
        ORDER BY d.ddate
        ROWS UNBOUNDED PRECEDING
      )
    WHEN :cum_scope = 'month' THEN
      SUM(d.ton) OVER (
        PARTITION BY DATE_TRUNC('month', d.ddate)
        ORDER BY d.ddate
        ROWS UNBOUNDED PRECEDING
      )
    WHEN :cum_scope = 'week' THEN
      SUM(d.ton) OVER (
        PARTITION BY d.iso_year, d.iso_week
        ORDER BY d.ddate
        ROWS UNBOUNDED PRECEDING
      )
    ELSE NULL
  END AS cum_ton
FROM d
ORDER BY d.ddate
