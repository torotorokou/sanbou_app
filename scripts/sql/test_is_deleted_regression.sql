-- ============================================================================
-- リグレッションテスト用SQL
-- 目的: is_deleted フィルタ適用前後で集計結果を比較する
-- ============================================================================

-- ============================================================================
-- Test 1: stg テーブルの論理削除状況の確認
-- ============================================================================
-- 各テーブルにおける論理削除行の分布を確認

SELECT
    'shogun_flash_receive' AS table_name,
    COUNT(*) AS total_rows,
    SUM(CASE WHEN is_deleted = false THEN 1 ELSE 0 END) AS active_rows,
    SUM(CASE WHEN is_deleted = true THEN 1 ELSE 0 END) AS deleted_rows,
    ROUND(100.0 * SUM(CASE WHEN is_deleted = true THEN 1 ELSE 0 END) / COUNT(*), 2) AS deleted_percent
FROM stg.shogun_flash_receive

UNION ALL

SELECT
    'shogun_final_receive' AS table_name,
    COUNT(*) AS total_rows,
    SUM(CASE WHEN is_deleted = false THEN 1 ELSE 0 END) AS active_rows,
    SUM(CASE WHEN is_deleted = true THEN 1 ELSE 0 END) AS deleted_rows,
    ROUND(100.0 * SUM(CASE WHEN is_deleted = true THEN 1 ELSE 0 END) / COUNT(*), 2) AS deleted_percent
FROM stg.shogun_final_receive

UNION ALL

SELECT
    'shogun_flash_yard' AS table_name,
    COUNT(*) AS total_rows,
    SUM(CASE WHEN is_deleted = false THEN 1 ELSE 0 END) AS active_rows,
    SUM(CASE WHEN is_deleted = true THEN 1 ELSE 0 END) AS deleted_rows,
    ROUND(100.0 * SUM(CASE WHEN is_deleted = true THEN 1 ELSE 0 END) / COUNT(*), 2) AS deleted_percent
FROM stg.shogun_flash_yard

UNION ALL

SELECT
    'shogun_final_yard' AS table_name,
    COUNT(*) AS total_rows,
    SUM(CASE WHEN is_deleted = false THEN 1 ELSE 0 END) AS active_rows,
    SUM(CASE WHEN is_deleted = true THEN 1 ELSE 0 END) AS deleted_rows,
    ROUND(100.0 * SUM(CASE WHEN is_deleted = true THEN 1 ELSE 0 END) / COUNT(*), 2) AS deleted_percent
FROM stg.shogun_final_yard

UNION ALL

SELECT
    'shogun_flash_shipment' AS table_name,
    COUNT(*) AS total_rows,
    SUM(CASE WHEN is_deleted = false THEN 1 ELSE 0 END) AS active_rows,
    SUM(CASE WHEN is_deleted = true THEN 1 ELSE 0 END) AS deleted_rows,
    ROUND(100.0 * SUM(CASE WHEN is_deleted = true THEN 1 ELSE 0 END) / COUNT(*), 2) AS deleted_percent
FROM stg.shogun_flash_shipment

UNION ALL

SELECT
    'shogun_final_shipment' AS table_name,
    COUNT(*) AS total_rows,
    SUM(CASE WHEN is_deleted = false THEN 1 ELSE 0 END) AS active_rows,
    SUM(CASE WHEN is_deleted = true THEN 1 ELSE 0 END) AS deleted_rows,
    ROUND(100.0 * SUM(CASE WHEN is_deleted = true THEN 1 ELSE 0 END) / COUNT(*), 2) AS deleted_percent
FROM stg.shogun_final_shipment

ORDER BY table_name;


-- ============================================================================
-- Test 2: slip_date 別の論理削除状況（直近30日分）
-- ============================================================================
-- 特定日付で論理削除が発生しているかを確認

SELECT
    slip_date,
    COUNT(*) AS total_rows,
    SUM(CASE WHEN is_deleted = false THEN 1 ELSE 0 END) AS active_rows,
    SUM(CASE WHEN is_deleted = true THEN 1 ELSE 0 END) AS deleted_rows,
    ROUND(100.0 * SUM(CASE WHEN is_deleted = true THEN 1 ELSE 0 END) / COUNT(*), 2) AS deleted_percent
FROM stg.shogun_flash_receive
WHERE slip_date IS NOT NULL
GROUP BY slip_date
ORDER BY slip_date DESC
LIMIT 30;


-- ============================================================================
-- Test 3: 日次集計の比較（is_deleted フィルタあり／なし）
-- ============================================================================
-- mart.v_receive_daily の結果が is_deleted フィルタでどう変わるかを検証

WITH
-- フィルタなし（旧ロジック）
unfiltered AS (
    SELECT
        s.slip_date AS ddate,
        SUM(s.net_weight) / 1000.0 AS receive_ton_unfiltered,
        COUNT(DISTINCT s.receive_no) AS vehicle_count_unfiltered
    FROM stg.shogun_flash_receive s
    WHERE s.slip_date IS NOT NULL
    GROUP BY s.slip_date
),
-- フィルタあり（新ロジック）
filtered AS (
    SELECT
        s.slip_date AS ddate,
        SUM(s.net_weight) / 1000.0 AS receive_ton_filtered,
        COUNT(DISTINCT s.receive_no) AS vehicle_count_filtered
    FROM stg.shogun_flash_receive s
    WHERE s.slip_date IS NOT NULL
      AND s.is_deleted = false
    GROUP BY s.slip_date
)
SELECT
    COALESCE(u.ddate, f.ddate) AS slip_date,
    COALESCE(u.receive_ton_unfiltered, 0) AS ton_unfiltered,
    COALESCE(f.receive_ton_filtered, 0) AS ton_filtered,
    COALESCE(u.receive_ton_unfiltered, 0) - COALESCE(f.receive_ton_filtered, 0) AS ton_diff,
    COALESCE(u.vehicle_count_unfiltered, 0) AS vehicles_unfiltered,
    COALESCE(f.vehicle_count_filtered, 0) AS vehicles_filtered,
    COALESCE(u.vehicle_count_unfiltered, 0) - COALESCE(f.vehicle_count_filtered, 0) AS vehicles_diff
FROM unfiltered u
FULL OUTER JOIN filtered f ON u.ddate = f.ddate
WHERE COALESCE(u.ddate, f.ddate) >= CURRENT_DATE - INTERVAL '30 days'
  AND (
    COALESCE(u.receive_ton_unfiltered, 0) <> COALESCE(f.receive_ton_filtered, 0)
    OR COALESCE(u.vehicle_count_unfiltered, 0) <> COALESCE(f.vehicle_count_filtered, 0)
  )
ORDER BY slip_date DESC
LIMIT 30;

-- 差異がなければ「No rows returned」となるはず（is_deleted = false のみのデータの場合）


-- ============================================================================
-- Test 4: active_* ビューの動作確認
-- ============================================================================
-- stg.active_shogun_flash_receive が正しく is_deleted = false を返すかを確認

SELECT
    'direct_table' AS source,
    COUNT(*) AS row_count
FROM stg.shogun_flash_receive
WHERE is_deleted = false

UNION ALL

SELECT
    'active_view' AS source,
    COUNT(*) AS row_count
FROM stg.active_shogun_flash_receive;

-- 両方の row_count が一致すればOK


-- ============================================================================
-- Test 5: mart.v_receive_daily の結果検証
-- ============================================================================
-- 更新後の mart.v_receive_daily から直近30日分のデータを取得

SELECT
    ddate,
    receive_net_ton,
    receive_vehicle_count,
    sales_yen,
    source_system,
    is_business,
    day_type
FROM mart.v_receive_daily
WHERE ddate >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY ddate DESC
LIMIT 30;


-- ============================================================================
-- Test 6: マテリアライズドビューのリフレッシュ後の検証
-- ============================================================================
-- mv_target_card_per_day の最新データを確認

SELECT
    ddate,
    day_target_ton,
    day_actual_ton_prev,
    week_actual_ton,
    month_actual_ton,
    is_business,
    day_type
FROM mart.mv_target_card_per_day
WHERE ddate >= CURRENT_DATE - INTERVAL '14 days'
ORDER BY ddate DESC;


-- ============================================================================
-- Test 7: インデックス使用状況の確認（EXPLAIN ANALYZE）
-- ============================================================================
-- 部分インデックスが正しく使われているかを確認

EXPLAIN ANALYZE
SELECT
    slip_date,
    COUNT(*) AS row_count,
    SUM(net_weight) / 1000.0 AS total_ton
FROM stg.shogun_flash_receive
WHERE slip_date >= CURRENT_DATE - INTERVAL '30 days'
  AND is_deleted = false
GROUP BY slip_date
ORDER BY slip_date DESC;

-- Expected: "Index Scan using idx_shogun_flash_receive_active" などが表示される


-- ============================================================================
-- Test 8: upload_file_id ごとの論理削除状況
-- ============================================================================
-- どのアップロードファイルが論理削除されているかを確認

SELECT
    upload_file_id,
    COUNT(*) AS total_rows,
    SUM(CASE WHEN is_deleted = false THEN 1 ELSE 0 END) AS active_rows,
    SUM(CASE WHEN is_deleted = true THEN 1 ELSE 0 END) AS deleted_rows,
    MIN(slip_date) AS min_slip_date,
    MAX(slip_date) AS max_slip_date
FROM stg.shogun_flash_receive
WHERE upload_file_id IS NOT NULL
GROUP BY upload_file_id
HAVING SUM(CASE WHEN is_deleted = true THEN 1 ELSE 0 END) > 0
ORDER BY upload_file_id DESC
LIMIT 20;


-- ============================================================================
-- Test 9: カレンダーAPIの結果確認
-- ============================================================================
-- mart.v_csv_calendar_union の結果を確認（論理削除された行が含まれないこと）

SELECT
    slip_date,
    csv_kind,
    row_count
FROM mart.v_csv_calendar_union
WHERE slip_date >= CURRENT_DATE - INTERVAL '30 days'
  AND csv_kind IN ('shogun_flash_receive', 'shogun_final_receive')
ORDER BY slip_date DESC, csv_kind;


-- ============================================================================
-- 実行方法
-- ============================================================================
--
-- ローカル環境での実行例:
-- docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
--   psql -U myuser -d sanbou_dev -f /path/to/this/file.sql
--
-- または:
-- psql -U myuser -h localhost -d sanbou_dev -f test_is_deleted_regression.sql
--
-- ============================================================================
