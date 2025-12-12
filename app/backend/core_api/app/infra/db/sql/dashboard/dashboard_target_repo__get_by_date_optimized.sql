-- dashboard_target_repo__get_by_date_optimized.sql
-- Optimized single-query fetch with anchor resolution and NULL masking.
-- Calculates cumulative and total targets for achievement modes.
--
-- Parameters:
--   :req - Target date (typically first day of month)
--   :mode - 'daily' or 'monthly'
--
-- Anchor logic (all in one SQL query):
-- - Current month: Use today (or month_end if today > month_end)
-- - Past month: Use month_end
-- - Future month: Use first business day (or month_start if none exists)
--
-- NULL masking (mode='monthly' and not current month):
-- - day_target_ton, week_target_ton, day_actual_ton_prev, week_actual_ton → NULL

WITH today AS (
  SELECT CURRENT_DATE::date AS today
),
bounds AS (
  SELECT
    date_trunc('month', CAST(:req AS DATE))::date AS month_start,
    (date_trunc('month', CAST(:req AS DATE)) + INTERVAL '1 month - 1 day')::date AS month_end
),
anchor AS (
  SELECT CASE
    -- Current month: use today (or month_end if today exceeds it)
    -- Note: day_actual_ton_prevは「ddate - 1 day」の実績を参照するため、
    --       今日の行を取得すれば「今日の目標 vs 昨日の実績」が得られる
    WHEN date_trunc('month', CAST(:req AS DATE)) = date_trunc('month', (SELECT today FROM today))
      THEN LEAST((SELECT today FROM today), (SELECT month_end FROM bounds))
    -- Past month: use month_end
    WHEN date_trunc('month', CAST(:req AS DATE)) < date_trunc('month', (SELECT today FROM today))
      THEN (SELECT month_end FROM bounds)
    -- Future month: use first business day (or month_start if none)
    ELSE COALESCE(
      (SELECT MIN(v.ddate)::date
       FROM mart.mv_receive_daily v
       WHERE v.ddate BETWEEN (SELECT month_start FROM bounds) AND (SELECT month_end FROM bounds)
         AND v.is_business = true),
      (SELECT month_start FROM bounds)
    )
  END AS ddate
),
base AS (
  SELECT
    v.ddate,
    v.day_target_ton, v.week_target_ton, v.month_target_ton,
    -- day_actual_ton_prevは「ddate - 1 day」の実績を参照
    -- 例: ddate=2025-12-12の場合、day_actual_ton_prev=2025-12-11の実績
    v.day_actual_ton_prev, v.week_actual_ton, v.month_actual_ton,
    v.iso_year, v.iso_week, v.iso_dow, v.day_type, v.is_business
  FROM mart.mv_target_card_per_day v
  JOIN anchor a ON v.ddate = a.ddate
  LIMIT 1
),
-- アンカー日に基づく累積計算の終了日を決定
-- 当月: 昨日まで（today - 1）
-- 過去月: 月末まで（month_end）※月末日を含む
-- 未来月: first_business_day の前日（ただし月初より前にならないよう調整）
cumulative_end_date AS (
  SELECT 
    CASE
      -- 当月の場合: 昨日まで（today - 1）
      WHEN date_trunc('month', CAST(:req AS DATE)) = date_trunc('month', (SELECT today FROM today))
        THEN GREATEST(
          ((SELECT today FROM today) - INTERVAL '1 day')::date,
          (SELECT month_start FROM bounds)
        )
      -- 過去月の場合: 月末まで（month_end）※月末日の実績を含める
      WHEN date_trunc('month', CAST(:req AS DATE)) < date_trunc('month', (SELECT today FROM today))
        THEN (SELECT month_end FROM bounds)
      -- 未来月の場合: アンカー日（first_business_day）の前日、ただし月初より前にならない
      ELSE GREATEST(
        ((SELECT ddate FROM anchor) - INTERVAL '1 day')::date,
        (SELECT month_start FROM bounds)
      )
    END AS cumulative_end_date
),
-- Calculate month cumulative target (sum of day_target_ton from month_start to cumulative_end_date)
-- 選択月内のみを対象とする
month_target_to_date AS (
  SELECT COALESCE(SUM(v.day_target_ton), 0)::numeric AS month_target_to_date_ton
  FROM mart.mv_target_card_per_day v
  WHERE v.ddate BETWEEN (SELECT month_start FROM bounds) AND (SELECT cumulative_end_date FROM cumulative_end_date)
),
-- Calculate month total target (max of month_target_ton for the entire month)
month_target_total AS (
  SELECT COALESCE(MAX(v.month_target_ton), 0)::numeric AS month_target_total_ton
  FROM mart.mv_target_card_per_day v
  WHERE v.ddate BETWEEN (SELECT month_start FROM bounds) AND (SELECT month_end FROM bounds)
),
-- Calculate week cumulative target (sum of day_target_ton from week_start to cumulative_end_date, same iso_year/iso_week)
-- 選択月内かつ同一週のみを対象とする
week_target_to_date AS (
  SELECT COALESCE(SUM(v.day_target_ton), 0)::numeric AS week_target_to_date_ton
  FROM mart.mv_target_card_per_day v, base b
  WHERE v.iso_year = b.iso_year
    AND v.iso_week = b.iso_week
    AND v.ddate >= (SELECT month_start FROM bounds)
    AND v.ddate <= (SELECT cumulative_end_date FROM cumulative_end_date)
),
-- Calculate week total target (max of week_target_ton for the entire week)
-- 週全体だが選択月内のみ
week_target_total AS (
  SELECT COALESCE(MAX(v.week_target_ton), 0)::numeric AS week_target_total_ton
  FROM mart.mv_target_card_per_day v, base b
  WHERE v.iso_year = b.iso_year
    AND v.iso_week = b.iso_week
    AND v.ddate >= (SELECT month_start FROM bounds)
    AND v.ddate <= (SELECT month_end FROM bounds)
),
-- Calculate month cumulative actual (sum of receive_net_ton from month_start to cumulative_end_date)
-- 選択月内のみを対象とする
month_actual_to_date AS (
  SELECT COALESCE(SUM(r.receive_net_ton), 0)::numeric AS month_actual_to_date_ton
  FROM mart.mv_receive_daily r
  WHERE r.ddate BETWEEN (SELECT month_start FROM bounds) AND (SELECT cumulative_end_date FROM cumulative_end_date)
),
-- Calculate week cumulative actual (sum of receive_net_ton from week_start to cumulative_end_date, same iso_year/iso_week)
-- 選択月内かつ同一週のみを対象とする
week_actual_to_date AS (
  SELECT COALESCE(SUM(r.receive_net_ton), 0)::numeric AS week_actual_to_date_ton
  FROM mart.mv_receive_daily r, base b
  WHERE r.iso_year = b.iso_year
    AND r.iso_week = b.iso_week
    AND r.ddate >= (SELECT month_start FROM bounds)
    AND r.ddate <= (SELECT cumulative_end_date FROM cumulative_end_date)
)
SELECT
  b.ddate,
  -- Apply NULL masking for day/week fields when mode=monthly and not current month
  CASE
    WHEN :mode = 'monthly'
     AND date_trunc('month', CAST(:req AS DATE)) <> date_trunc('month', (SELECT today FROM today))
    THEN NULL ELSE b.day_target_ton END AS day_target_ton,
  CASE
    WHEN :mode = 'monthly'
     AND date_trunc('month', CAST(:req AS DATE)) <> date_trunc('month', (SELECT today FROM today))
    THEN NULL ELSE b.week_target_ton END AS week_target_ton,
  b.month_target_ton,
  CASE
    WHEN :mode = 'monthly'
     AND date_trunc('month', CAST(:req AS DATE)) <> date_trunc('month', (SELECT today FROM today))
    THEN NULL ELSE b.day_actual_ton_prev END AS day_actual_ton_prev,
  CASE
    WHEN :mode = 'monthly'
     AND date_trunc('month', CAST(:req AS DATE)) <> date_trunc('month', (SELECT today FROM today))
    THEN NULL ELSE b.week_actual_ton END AS week_actual_ton,
  b.month_actual_ton,
  b.iso_year, b.iso_week, b.iso_dow, b.day_type, b.is_business,
  -- New cumulative and total target fields
  (SELECT month_target_to_date_ton FROM month_target_to_date) AS month_target_to_date_ton,
  (SELECT month_target_total_ton FROM month_target_total) AS month_target_total_ton,
  (SELECT week_target_to_date_ton FROM week_target_to_date) AS week_target_to_date_ton,
  (SELECT week_target_total_ton FROM week_target_total) AS week_target_total_ton,
  (SELECT month_actual_to_date_ton FROM month_actual_to_date) AS month_actual_to_date_ton,
  (SELECT week_actual_to_date_ton FROM week_actual_to_date) AS week_actual_to_date_ton
FROM base b;
