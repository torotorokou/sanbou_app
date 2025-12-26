-- ============================================================
-- 99_verify.sql - 検証クエリ
-- ============================================================
--
-- 目的: 権限整備が正しく適用されたことを確認
--
-- 実行方法:
--   psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f 99_verify.sql
-- ============================================================

\set ON_ERROR_STOP 0

\echo ''
\echo '================================================================'
\echo '99_verify.sql - 検証'
\echo '================================================================'
\echo ''

-- ============================================================
-- 1. ロール確認
-- ============================================================
\echo '[1/7] ロール一覧'
\echo '--------------------------------------------------------------'

SELECT
  rolname,
  CASE WHEN rolsuper THEN '✓' ELSE ' ' END as superuser,
  CASE WHEN rolcanlogin THEN '✓' ELSE ' ' END as login,
  CASE WHEN rolcreaterole THEN '✓' ELSE ' ' END as create_role,
  CASE WHEN rolcreatedb THEN '✓' ELSE ' ' END as create_db
FROM pg_roles
WHERE rolname NOT LIKE 'pg_%'
ORDER BY
  CASE
    WHEN rolname = 'sanbou_owner' THEN 1
    WHEN rolname LIKE 'sanbou_app_%' THEN 2
    WHEN rolname = 'app_readonly' THEN 3
    WHEN rolname = 'myuser' THEN 4
    ELSE 5
  END,
  rolname;

\echo ''
\echo '期待値:'
\echo '  - sanbou_owner: superuser=❌, login=❌'
\echo '  - sanbou_app_*: superuser=❌, login=✓'
\echo '  - app_readonly: superuser=❌, login=❌'
\echo '  - myuser: superuser=✓, login=✓ (break-glass用)'
\echo ''

-- ============================================================
-- 2. スキーマ owner 確認
-- ============================================================
\echo '[2/7] スキーマ owner 確認'
\echo '--------------------------------------------------------------'

SELECT
  nspname as schema_name,
  pg_catalog.pg_get_userbyid(nspowner) as owner,
  CASE
    WHEN pg_catalog.pg_get_userbyid(nspowner) = 'sanbou_owner' THEN '✓'
    ELSE '⚠️'
  END as status
FROM pg_namespace
WHERE nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
  AND nspname NOT LIKE 'pg_temp_%'
  AND nspname NOT LIKE 'pg_toast_temp_%'
ORDER BY nspname;

\echo ''
\echo '期待値: すべてのスキーマが sanbou_owner 所有（status=✓）'
\echo ''

-- ============================================================
-- 3. テーブル owner サンプル確認
-- ============================================================
\echo '[3/7] テーブル owner サンプル（各スキーマ先頭3件）'
\echo '--------------------------------------------------------------'

WITH table_samples AS (
  SELECT
    schemaname,
    tablename,
    tableowner,
    ROW_NUMBER() OVER (PARTITION BY schemaname ORDER BY tablename) as rn
  FROM pg_tables
  WHERE schemaname IN ('raw', 'stg', 'mart', 'ref', 'kpi', 'log', 'app', 'app_auth', 'forecast', 'jobs', 'sandbox', 'public')
)
SELECT
  schemaname,
  tablename,
  tableowner,
  CASE
    WHEN tableowner = 'sanbou_owner' THEN '✓'
    ELSE '⚠️'
  END as status
FROM table_samples
WHERE rn <= 3
ORDER BY schemaname, tablename;

\echo ''
\echo '期待値: すべてのテーブルが sanbou_owner 所有（status=✓）'
\echo ''

-- ============================================================
-- 4. シーケンス owner サンプル確認
-- ============================================================
\echo '[4/7] シーケンス owner サンプル（先頭10件）'
\echo '--------------------------------------------------------------'

SELECT
  schemaname,
  sequencename,
  sequenceowner,
  CASE
    WHEN sequenceowner = 'sanbou_owner' THEN '✓'
    ELSE '⚠️'
  END as status
FROM pg_sequences
WHERE schemaname IN ('raw', 'stg', 'mart', 'ref', 'kpi', 'log', 'app', 'app_auth', 'forecast', 'jobs', 'sandbox', 'public')
ORDER BY schemaname, sequencename
LIMIT 10;

\echo ''
\echo '期待値: すべてのシーケンスが sanbou_owner 所有（status=✓）'
\echo ''

-- ============================================================
-- 5. アプリユーザーの権限確認（テーブル）
-- ============================================================
\echo '[5/7] アプリユーザーのテーブル権限'
\echo '--------------------------------------------------------------'

SELECT
  table_schema,
  string_agg(DISTINCT privilege_type, ', ' ORDER BY privilege_type) as privileges,
  COUNT(DISTINCT table_name) as table_count
FROM information_schema.table_privileges
WHERE grantee = current_user
  AND table_schema IN ('raw', 'stg', 'mart', 'ref', 'kpi', 'log', 'app', 'app_auth', 'forecast', 'jobs', 'sandbox', 'public')
GROUP BY table_schema
ORDER BY
  CASE table_schema
    WHEN 'raw' THEN 1
    WHEN 'stg' THEN 2
    WHEN 'mart' THEN 3
    WHEN 'ref' THEN 4
    WHEN 'kpi' THEN 5
    WHEN 'log' THEN 6
    WHEN 'app' THEN 7
    WHEN 'app_auth' THEN 8
    WHEN 'forecast' THEN 9
    WHEN 'jobs' THEN 10
    WHEN 'sandbox' THEN 11
    WHEN 'public' THEN 12
    ELSE 99
  END;

\echo ''
\echo '期待値:'
\echo '  - raw, stg, kpi, log, app, app_auth, forecast, jobs, sandbox, public:'
\echo '    DELETE, INSERT, SELECT, UPDATE'
\echo '  - mart, ref: SELECT'
\echo ''

-- ============================================================
-- 6. シーケンス権限確認（重要）
-- ============================================================
\echo '[6/7] シーケンス権限確認（permission denied 防止）'
\echo '--------------------------------------------------------------'

WITH seq_privs AS (
  SELECT
    n.nspname as schema_name,
    c.relname as sequence_name,
    CASE
      WHEN has_sequence_privilege(current_user, c.oid, 'USAGE') THEN '✓'
      ELSE '❌'
    END as usage_priv,
    CASE
      WHEN has_sequence_privilege(current_user, c.oid, 'SELECT') THEN '✓'
      ELSE '❌'
    END as select_priv
  FROM pg_class c
  JOIN pg_namespace n ON n.oid = c.relnamespace
  WHERE c.relkind = 'S'
    AND n.nspname IN ('raw', 'stg', 'kpi', 'log', 'app', 'app_auth', 'forecast', 'jobs', 'sandbox', 'public')
)
SELECT
  schema_name,
  COUNT(*) as seq_count,
  SUM(CASE WHEN usage_priv = '✓' THEN 1 ELSE 0 END) as usage_ok,
  SUM(CASE WHEN select_priv = '✓' THEN 1 ELSE 0 END) as select_ok,
  CASE
    WHEN SUM(CASE WHEN usage_priv = '✓' THEN 1 ELSE 0 END) = COUNT(*)
     AND SUM(CASE WHEN select_priv = '✓' THEN 1 ELSE 0 END) = COUNT(*)
    THEN '✓ OK'
    ELSE '⚠️ NG'
  END as status
FROM seq_privs
GROUP BY schema_name
ORDER BY schema_name;

\echo ''
\echo '期待値: すべてのスキーマで USAGE と SELECT が全シーケンスに付与（status=✓ OK）'
\echo ''

-- ============================================================
-- 7. デフォルト権限確認
-- ============================================================
\echo '[7/7] デフォルト権限設定確認'
\echo '--------------------------------------------------------------'

SELECT
  defaclnamespace::regnamespace as schema,
  defaclobjtype as obj_type,
  pg_catalog.pg_get_userbyid(defaclrole) as for_role,
  defaclacl as default_acl
FROM pg_default_acl
WHERE defaclnamespace IN (
  SELECT oid FROM pg_namespace
  WHERE nspname IN ('raw', 'stg', 'mart', 'ref', 'kpi', 'log', 'app', 'app_auth', 'forecast', 'jobs', 'sandbox', 'public')
)
ORDER BY schema, obj_type;

\echo ''
\echo '期待値:'
\echo '  - sanbou_owner が各スキーマで作成するオブジェクトに対して'
\echo '    アプリユーザーへの自動権限付与が設定されている'
\echo '  - obj_type: r (table), S (sequence), f (function)'
\echo ''

\echo '================================================================'
\echo '検証完了'
\echo '================================================================'
\echo ''
\echo '✅ チェックリスト:'
\echo '  [ ] sanbou_owner ロールが存在'
\echo '  [ ] すべてのスキーマが sanbou_owner 所有'
\echo '  [ ] すべてのテーブルが sanbou_owner 所有'
\echo '  [ ] すべてのシーケンスが sanbou_owner 所有'
\echo '  [ ] アプリユーザーが適切なテーブル権限を持つ'
\echo '  [ ] シーケンスへの USAGE, SELECT 権限あり'
\echo '  [ ] デフォルト権限が設定されている'
\echo ''
\echo '⚠️  もし「⚠️ NG」や「❌」が表示された場合:'
\echo '   1. 03_grants.sql を再実行'
\echo '   2. 04_default_privileges.sql を再実行'
\echo '   3. この検証SQLを再実行'
\echo ''

\set ON_ERROR_STOP 1
