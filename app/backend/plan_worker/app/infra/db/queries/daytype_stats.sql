-- $1: window_start, $2: window_end, $3: lookback_years
WITH hist AS (
  SELECT d.ddate::date AS ddate, d.ton_in::numeric AS ton
  FROM mart.receive_daily_ton d
  WHERE d.ddate BETWEEN ($2 - ($3 || ' years')::interval)::date AND $2
),
joined AS (
  SELECT h.ddate, h.ton, c.day_type, c.is_company_closed
  FROM hist h
  JOIN ref.v_calendar_classified c ON c.ddate = h.ddate
  WHERE NOT c.is_company_closed
)
SELECT day_type, COUNT(*) AS sample_days, AVG(ton)::numeric AS mean_ton
FROM joined
GROUP BY day_type
ORDER BY day_type;
