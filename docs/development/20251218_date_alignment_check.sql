-- =====================================================================
-- 日付整合性検証SQL
-- 作成日: 2025-12-18
-- 目的: stg受入データと mart予約データの日付範囲・当日含有・整合性を検証
-- =====================================================================

-- 使用方法:
-- psql -U myuser -d sanbou_dev -v target_date='2025-12-18' -f this_file.sql
-- または psql内で:
-- \set target_date '2025-12-18'
-- \i this_file.sql

\echo ''
\echo '========================================='
\echo '日付整合性検証: 対象日 = ' :target_date
\echo '========================================='
\echo ''

-- =====================================================================
-- 1-A) stg受入：範囲と件数（360日前後、前日まで）
-- =====================================================================
\echo '【1-A】stg.v_active_shogun_flash_receive: データ範囲と件数'
\echo '期待: 過去360日前後、当日は含まない（前日まで）'
\echo ''

WITH base AS (
  SELECT
    slip_date::date AS d
  FROM stg.v_active_shogun_flash_receive
  WHERE slip_date >= (:'target_date'::date - INTERVAL '360 days')::date
    AND slip_date <= (:'target_date'::date - INTERVAL '1 day')::date
)
SELECT
  MIN(d) AS min_date,
  MAX(d) AS max_date,
  COUNT(*) AS total_rows,
  COUNT(DISTINCT d) AS distinct_days,
  (:'target_date'::date - MIN(d))::int AS days_from_min,
  (:'target_date'::date - MAX(d))::int AS days_from_max
FROM base;

\echo ''

-- =====================================================================
-- 1-B) mart予約：範囲と件数（361日前後、当日含む）
-- =====================================================================
\echo '【1-B】mart.v_reserve_daily_for_forecast: データ範囲と件数'
\echo '期待: 過去360日前後、当日を含む（361日分）'
\echo ''

WITH base AS (
  SELECT
    date::date AS d,
    reserve_trucks,
    reserve_fixed_trucks
  FROM mart.v_reserve_daily_for_forecast
  WHERE date >= (:'target_date'::date - INTERVAL '360 days')::date
    AND date <= :'target_date'::date
)
SELECT
  MIN(d) AS min_date,
  MAX(d) AS max_date,
  COUNT(*) AS total_rows,
  COUNT(DISTINCT d) AS distinct_days,
  SUM(CASE WHEN d = :'target_date'::date THEN 1 ELSE 0 END) AS rows_on_target_date,
  (:'target_date'::date - MIN(d))::int AS days_from_min,
  (MAX(d) - :'target_date'::date)::int AS days_beyond_target
FROM base;

\echo ''

-- =====================================================================
-- 2-A) 予約は当日が存在するか（NULL/0区別も）
-- =====================================================================
\echo '【2-A】予約：当日データの存在確認'
\echo '期待: 1行存在、trucks値が0またはPOSITIVE'
\echo ''

SELECT
  date AS reserve_day,
  reserve_trucks,
  reserve_fixed_trucks,
  CASE
    WHEN reserve_trucks IS NULL THEN 'NULL(未記入の疑い)'
    WHEN reserve_trucks = 0 THEN '0(ゼロ)'
    ELSE 'POSITIVE'
  END AS trucks_state
FROM mart.v_reserve_daily_for_forecast
WHERE date = :'target_date'::date;

\echo ''

-- =====================================================================
-- 2-B) stg受入は当日が混入していないか
-- =====================================================================
\echo '【2-B】受入：当日データの混入チェック'
\echo '期待: 0行（当日データなし）'
\echo ''

SELECT
  COUNT(*) AS rows_on_target_date,
  CASE
    WHEN COUNT(*) = 0 THEN 'OK: 当日データなし'
    ELSE 'NG: 当日データが混入'
  END AS status
FROM stg.v_active_shogun_flash_receive
WHERE slip_date = :'target_date'::date;

\echo ''

-- =====================================================================
-- 3-A) 両者の日付集合を比較してズレ日を抽出
-- =====================================================================
\echo '【3-A】日付集合差分：両者に存在しない日付を検出'
\echo '期待: 0行（差分なし）'
\echo ''

WITH recv_days AS (
  SELECT DISTINCT slip_date::date AS d
  FROM stg.v_active_shogun_flash_receive
  WHERE slip_date >= (:'target_date'::date - INTERVAL '360 days')::date
    AND slip_date <= (:'target_date'::date - INTERVAL '1 day')::date
),
resv_days AS (
  SELECT DISTINCT date::date AS d
  FROM mart.v_reserve_daily_for_forecast
  WHERE date >= (:'target_date'::date - INTERVAL '360 days')::date
    AND date <= :'target_date'::date
)
SELECT 
  'recv_only' AS side, 
  d,
  to_char(d, 'Day') AS day_of_week
FROM recv_days
WHERE d NOT IN (SELECT d FROM resv_days)
UNION ALL
SELECT 
  'resv_only' AS side, 
  d,
  to_char(d, 'Day') AS day_of_week
FROM resv_days
WHERE d NOT IN (SELECT d FROM recv_days)
ORDER BY side, d;

\echo ''
\echo '========================================='
\echo '検証完了'
\echo '========================================='
