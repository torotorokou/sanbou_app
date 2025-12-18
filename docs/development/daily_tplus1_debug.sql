-- ==============================================================================
-- 日次t+1予測デバッグ用SQL：異常値（1トン等）の原因調査
-- ==============================================================================
-- 目的：予測値が1トンなど異常になる原因をDB側から検証する
-- 実行環境：sanbou_dev
-- 実行日：2025-12-18
-- ==============================================================================

-- ==============================================================================
-- 1. 実績データ（mart.mv_receive_daily or stg.shogun_final_receive）の確認
-- ==============================================================================

\echo '=========================================='
\echo '1-1. 実績データの基本統計（直近400日）'
\echo '=========================================='

-- 現在使用しているテーブル：stg.shogun_final_receive
SELECT
    '実績データ（stg.shogun_final_receive）' AS data_source,
    MIN(伝票日付) AS min_date,
    MAX(伝票日付) AS max_date,
    COUNT(*) AS total_rows,
    COUNT(DISTINCT 伝票日付) AS distinct_dates,
    -- 正味重量の統計（kg単位）
    MIN(正味重量) AS min_weight_kg,
    MAX(正味重量) AS max_weight_kg,
    AVG(正味重量) AS avg_weight_kg,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY 正味重量) AS median_weight_kg,
    -- 1トン未満の異常値チェック
    SUM(CASE WHEN 正味重量 < 1000 THEN 1 ELSE 0 END) AS rows_less_than_1ton,
    SUM(CASE WHEN 正味重量 <= 0 THEN 1 ELSE 0 END) AS rows_zero_or_negative
FROM stg.shogun_final_receive
WHERE 伝票日付 >= CURRENT_DATE - INTERVAL '400 days';

\echo ''
\echo '=========================================='
\echo '1-2. 直近10日の日次集計（ton単位に変換）'
\echo '=========================================='

SELECT
    伝票日付 AS date,
    COUNT(*) AS row_count,
    SUM(正味重量) / 1000.0 AS total_weight_ton,
    AVG(正味重量) / 1000.0 AS avg_weight_ton,
    MIN(正味重量) / 1000.0 AS min_weight_ton,
    MAX(正味重量) / 1000.0 AS max_weight_ton
FROM stg.shogun_final_receive
WHERE 伝票日付 >= CURRENT_DATE - INTERVAL '10 days'
GROUP BY 伝票日付
ORDER BY 伝票日付 DESC;

\echo ''
\echo '=========================================='
\echo '1-3. 品目別の統計（top10）'
\echo '=========================================='

SELECT
    品目コード,
    品目名称,
    COUNT(*) AS row_count,
    SUM(正味重量) / 1000.0 AS total_weight_ton,
    AVG(正味重量) / 1000.0 AS avg_weight_ton
FROM stg.shogun_final_receive
WHERE 伝票日付 >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY 品目コード, 品目名称
ORDER BY total_weight_ton DESC
LIMIT 10;

-- ==============================================================================
-- 2. 予約データ（mart.v_reserve_daily_for_forecast）の確認
-- ==============================================================================

\echo ''
\echo '=========================================='
\echo '2-1. 予約ビューの基本情報'
\echo '=========================================='

SELECT
    MIN(reserve_date) AS min_reserve_date,
    MAX(reserve_date) AS max_reserve_date,
    COUNT(*) AS total_rows,
    COUNT(DISTINCT reserve_date) AS distinct_dates
FROM mart.v_reserve_daily_for_forecast;

\echo ''
\echo '=========================================='
\echo '2-2. 今日と明日の予約データ'
\echo '=========================================='

SELECT
    reserve_date,
    trucks,
    fixed_trucks,
    trucks IS NULL AS trucks_is_null,
    fixed_trucks IS NULL AS fixed_trucks_is_null
FROM mart.v_reserve_daily_for_forecast
WHERE reserve_date >= CURRENT_DATE
  AND reserve_date <= CURRENT_DATE + INTERVAL '1 day'
ORDER BY reserve_date;

\echo ''
\echo '=========================================='
\echo '2-3. 直近30日の予約統計'
\echo '=========================================='

SELECT
    reserve_date,
    trucks,
    fixed_trucks,
    COALESCE(trucks, 0) AS trucks_with_default,
    COALESCE(fixed_trucks, 0) AS fixed_trucks_with_default
FROM mart.v_reserve_daily_for_forecast
WHERE reserve_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY reserve_date DESC
LIMIT 30;

-- ==============================================================================
-- 3. 学習範囲の検証（要件：昨日まで360日）
-- ==============================================================================

\echo ''
\echo '=========================================='
\echo '3-1. target_date = CURRENT_DATE として学習範囲を確認'
\echo '=========================================='

WITH params AS (
    SELECT
        CURRENT_DATE AS target_date,
        365 AS lookback_days
)
SELECT
    p.target_date,
    p.target_date - 1 AS training_end_date,
    p.target_date - p.lookback_days AS training_start_date,
    -- この範囲のデータ件数
    (SELECT COUNT(*)
     FROM stg.shogun_final_receive
     WHERE 伝票日付 >= p.target_date - p.lookback_days
       AND 伝票日付 <= p.target_date - 1) AS training_rows,
    -- この範囲の日数
    (SELECT COUNT(DISTINCT 伝票日付)
     FROM stg.shogun_final_receive
     WHERE 伝票日付 >= p.target_date - p.lookback_days
       AND 伝票日付 <= p.target_date - 1) AS training_days,
    -- 予約の有無
    (SELECT COUNT(*)
     FROM mart.v_reserve_daily_for_forecast
     WHERE reserve_date = p.target_date) AS reserve_exists
FROM params p;

\echo ''
\echo '=========================================='
\echo '3-2. target_date = CURRENT_DATE + 1 として学習範囲を確認'
\echo '=========================================='

WITH params AS (
    SELECT
        CURRENT_DATE + 1 AS target_date,
        365 AS lookback_days
)
SELECT
    p.target_date,
    p.target_date - 1 AS training_end_date,
    p.target_date - p.lookback_days AS training_start_date,
    -- この範囲のデータ件数
    (SELECT COUNT(*)
     FROM stg.shogun_final_receive
     WHERE 伝票日付 >= p.target_date - p.lookback_days
       AND 伝票日付 <= p.target_date - 1) AS training_rows,
    -- この範囲の日数
    (SELECT COUNT(DISTINCT 伝票日付)
     FROM stg.shogun_final_receive
     WHERE 伝票日付 >= p.target_date - p.lookback_days
       AND 伝票日付 <= p.target_date - 1) AS training_days,
    -- 予約の有無
    (SELECT COUNT(*)
     FROM mart.v_reserve_daily_for_forecast
     WHERE reserve_date = p.target_date) AS reserve_exists
FROM params p;

-- ==============================================================================
-- 4. 単位変換の検証
-- ==============================================================================

\echo ''
\echo '=========================================='
\echo '4-1. 単位変換前後の比較（サンプル：直近5日）'
\echo '=========================================='

SELECT
    伝票日付 AS date,
    正味重量 AS raw_weight_value,
    正味重量 / 1000.0 AS converted_to_ton,
    CASE
        WHEN 正味重量 < 1000 THEN 'SUSPICIOUS: less than 1 ton'
        WHEN 正味重量 > 100000 THEN 'SUSPICIOUS: more than 100 ton'
        ELSE 'OK'
    END AS validation
FROM stg.shogun_final_receive
WHERE 伝票日付 >= CURRENT_DATE - INTERVAL '5 days'
ORDER BY 伝票日付 DESC, 正味重量 DESC
LIMIT 20;

-- ==============================================================================
-- 5. 最近実行されたジョブの確認
-- ==============================================================================

\echo ''
\echo '=========================================='
\echo '5-1. 最近のジョブ実行結果'
\echo '=========================================='

SELECT
    fj.id AS job_id,
    fj.target_date,
    fj.status,
    fj.started_at,
    fj.finished_at,
    EXTRACT(EPOCH FROM (fj.finished_at - fj.started_at)) AS duration_seconds,
    dfr.p50,
    dfr.p10,
    dfr.p90,
    dfr.unit,
    dfr.input_snapshot->>'actuals_count' AS actuals_count,
    dfr.input_snapshot->>'reserve_count' AS reserve_count,
    dfr.input_snapshot->>'actuals_start_date' AS actuals_start,
    dfr.input_snapshot->>'actuals_end_date' AS actuals_end
FROM forecast.forecast_jobs fj
LEFT JOIN forecast.daily_forecast_results dfr ON fj.id = dfr.job_id
WHERE fj.job_type = 'daily_tplus1'
ORDER BY fj.created_at DESC
LIMIT 10;

\echo ''
\echo '完了：すべての検証SQLが実行されました'
