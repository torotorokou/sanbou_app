-- ================================================================
-- client_cd 正規化処理の検証SQL
-- ================================================================
--
-- 目的: 20251224_004 マイグレーション実行後の検証
-- 実行タイミング: make al-up-env 実行後
--
-- 期待結果:
--   1. 先頭0残存件数: 0件
--   2. 末尾X残存件数（view）: 0件
--   3. 正規化関数の動作: 正常
--
-- ================================================================

\echo '================================================================'
\echo 'client_cd 正規化処理 検証SQL'
\echo '================================================================'
\echo ''

-- ================================================================
-- 1. 先頭0残存件数の確認（テーブル）
-- ================================================================
\echo '[1/6] 先頭0残存件数の確認（0件のはず）'
\echo '--------------------------------------------------------------'

SELECT
  'shogun_flash_receive' as table_name,
  COUNT(*) as leading_zero_count,
  CASE
    WHEN COUNT(*) = 0 THEN '✅ OK'
    ELSE '❌ NG - 先頭0が残っています'
  END as status
FROM stg.shogun_flash_receive
WHERE btrim(client_cd) ~ '^0[0-9]'
UNION ALL
SELECT
  'shogun_final_receive' as table_name,
  COUNT(*) as leading_zero_count,
  CASE
    WHEN COUNT(*) = 0 THEN '✅ OK'
    ELSE '❌ NG - 先頭0が残っています'
  END as status
FROM stg.shogun_final_receive
WHERE btrim(client_cd) ~ '^0[0-9]';

\echo ''
\echo '期待: 両方とも 0件'
\echo ''

-- ================================================================
-- 2. 正規化関数の動作確認
-- ================================================================
\echo '[2/6] stg.normalize_client_cd() 関数の動作確認'
\echo '--------------------------------------------------------------'

SELECT
  '001021' as input,
  stg.normalize_client_cd('001021') as output,
  '1021' as expected,
  CASE
    WHEN stg.normalize_client_cd('001021') = '1021' THEN '✅ OK'
    ELSE '❌ NG'
  END as status
UNION ALL
SELECT
  '00169X' as input,
  stg.normalize_client_cd('00169X') as output,
  '169X' as expected,
  CASE
    WHEN stg.normalize_client_cd('00169X') = '169X' THEN '✅ OK'
    ELSE '❌ NG'
  END as status
UNION ALL
SELECT
  '0000' as input,
  stg.normalize_client_cd('0000') as output,
  '0' as expected,
  CASE
    WHEN stg.normalize_client_cd('0000') = '0' THEN '✅ OK'
    ELSE '❌ NG'
  END as status
UNION ALL
SELECT
  'NULL' as input,
  COALESCE(stg.normalize_client_cd(NULL), 'NULL') as output,
  'NULL' as expected,
  CASE
    WHEN stg.normalize_client_cd(NULL) IS NULL THEN '✅ OK'
    ELSE '❌ NG'
  END as status
UNION ALL
SELECT
  ' 001234 ' as input,
  stg.normalize_client_cd(' 001234 ') as output,
  '1234' as expected,
  CASE
    WHEN stg.normalize_client_cd(' 001234 ') = '1234' THEN '✅ OK'
    ELSE '❌ NG'
  END as status;

\echo ''

-- ================================================================
-- 3. 末尾X除去確認（view）
-- ================================================================
\echo '[3/6] v_active_* ビューでの末尾X除去確認'
\echo '--------------------------------------------------------------'

WITH final_view_x_check AS (
  SELECT
    client_cd,
    COUNT(*) as count
  FROM stg.v_active_shogun_final_receive
  WHERE client_cd ~ '[Xx]$'
  GROUP BY client_cd
)
SELECT
  'v_active_shogun_final_receive' as view_name,
  COALESCE(SUM(count), 0) as trailing_x_count,
  CASE
    WHEN COALESCE(SUM(count), 0) = 0 THEN '✅ OK - 末尾Xが除去されています'
    ELSE '❌ NG - 末尾Xが残っています'
  END as status
FROM final_view_x_check;

\echo ''

-- ================================================================
-- 4. バックアップテーブルの存在確認
-- ================================================================
\echo '[4/6] バックアップテーブルの存在確認'
\echo '--------------------------------------------------------------'

SELECT
  tablename,
  'stg' as schema,
  'backup' as type
FROM pg_tables
WHERE schemaname = 'stg'
  AND tablename LIKE '%client_cd_backup_%'
ORDER BY tablename;

\echo ''
\echo '期待: 2つのバックアップテーブルが存在'
\echo ''

-- ================================================================
-- 5. 更新前後のサンプル比較（バックアップテーブルから）
-- ================================================================
\echo '[5/6] 更新前後のサンプル比較（先頭10件）'
\echo '--------------------------------------------------------------'

-- Note: バックアップテーブル名に実際のタイムスタンプが含まれるため、
--       存在する最新のバックアップテーブルを動的に取得

DO $$
DECLARE
    backup_table_flash text;
    backup_table_final text;
BEGIN
    -- 最新のバックアップテーブル名を取得
    SELECT tablename INTO backup_table_flash
    FROM pg_tables
    WHERE schemaname = 'stg'
      AND tablename LIKE 'shogun_flash_receive_client_cd_backup_%'
    ORDER BY tablename DESC
    LIMIT 1;

    SELECT tablename INTO backup_table_final
    FROM pg_tables
    WHERE schemaname = 'stg'
      AND tablename LIKE 'shogun_final_receive_client_cd_backup_%'
    ORDER BY tablename DESC
    LIMIT 1;

    IF backup_table_flash IS NOT NULL THEN
        RAISE NOTICE 'shogun_flash_receive サンプル比較:';
        RAISE NOTICE '--------------------------------------------------------------';
        EXECUTE format('
            SELECT
              t.id,
              b.old_client_cd as before,
              t.client_cd as after
            FROM stg.shogun_flash_receive t
            JOIN stg.%I b ON t.id = b.id
            ORDER BY t.id
            LIMIT 10;
        ', backup_table_flash);
    END IF;

    IF backup_table_final IS NOT NULL THEN
        RAISE NOTICE '';
        RAISE NOTICE 'shogun_final_receive サンプル比較:';
        RAISE NOTICE '--------------------------------------------------------------';
        EXECUTE format('
            SELECT
              t.id,
              b.old_client_cd as before,
              t.client_cd as after
            FROM stg.shogun_final_receive t
            JOIN stg.%I b ON t.id = b.id
            ORDER BY t.id
            LIMIT 10;
        ', backup_table_final);
    END IF;
END $$;

\echo ''

-- ================================================================
-- 6. 統計サマリー
-- ================================================================
\echo '[6/6] 統計サマリー'
\echo '--------------------------------------------------------------'

WITH flash_stats AS (
  SELECT
    'shogun_flash_receive' as table_name,
    COUNT(*) as total_rows,
    COUNT(DISTINCT client_cd) as unique_client_cd,
    MIN(LENGTH(client_cd)) as min_length,
    MAX(LENGTH(client_cd)) as max_length
  FROM stg.shogun_flash_receive
  WHERE client_cd IS NOT NULL
),
final_stats AS (
  SELECT
    'shogun_final_receive' as table_name,
    COUNT(*) as total_rows,
    COUNT(DISTINCT client_cd) as unique_client_cd,
    MIN(LENGTH(client_cd)) as min_length,
    MAX(LENGTH(client_cd)) as max_length
  FROM stg.shogun_final_receive
  WHERE client_cd IS NOT NULL
)
SELECT * FROM flash_stats
UNION ALL
SELECT * FROM final_stats;

\echo ''
\echo '================================================================'
\echo '検証完了'
\echo '================================================================'
\echo ''
\echo '✅ チェックリスト:'
\echo '  [ ] 先頭0残存件数が0件'
\echo '  [ ] 正規化関数が正常動作'
\echo '  [ ] view で末尾Xが除去されている'
\echo '  [ ] バックアップテーブルが存在'
\echo '  [ ] 更新前後のサンプルで正規化確認'
\echo ''
