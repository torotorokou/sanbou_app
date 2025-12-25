-- ==============================================================================
-- 環境別アプリケーション用DBユーザー作成SQL
-- ==============================================================================
--
-- 【目的】
-- 環境ごとに専用のアプリケーション用DBユーザーを作成し、最小権限の原則に従って
-- 必要な権限のみを付与します。
--
-- 【前提条件】
-- 1. myuser のパスワードが強力なものに変更済みであること
-- 2. 各環境のデータベース（sanbou_dev / sanbou_stg / sanbou_prod）が存在すること
-- 3. 環境別の強力なパスワードを生成済みであること（openssl rand -base64 32）
--
-- 【実行方法】
-- 環境ごとに該当するセクションを実行してください。
-- 実行前に <PLACEHOLDER> を実際のパスワードに置き換えてください。
--
-- 例：開発環境
-- psql -U myuser -d sanbou_dev -f 20251204_create_app_db_users.sql
--
-- または docker compose 経由で：
-- docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
--   psql -U myuser -d sanbou_dev < scripts/sql/20251204_create_app_db_users.sql
--
-- 【注意事項】
-- ・このファイルはGit管理されます。実際のパスワードは書き込まないでください
-- ・本番環境では必ず異なるパスワードを使用してください
-- ・パスワードは secrets/.env.*.secrets ファイルにも同じ値を設定してください
--
-- ==============================================================================

\echo '=========================================='
\echo '環境別アプリケーション用DBユーザー作成'
\echo '=========================================='
\echo ''

-- ==============================================================================
-- 開発環境（sanbou_dev）
-- ==============================================================================

\echo '▶ 開発環境ユーザー (sanbou_app_dev) を作成...'

-- ユーザー作成（既に存在する場合はスキップ）
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'sanbou_app_dev') THEN
        CREATE USER sanbou_app_dev WITH PASSWORD '<DEV_DB_PASSWORD_PLACEHOLDER>';
        RAISE NOTICE 'ユーザー sanbou_app_dev を作成しました';
    ELSE
        RAISE NOTICE 'ユーザー sanbou_app_dev は既に存在します';
        -- パスワードのみ更新する場合は以下をアンコメント
        -- ALTER USER sanbou_app_dev WITH PASSWORD '<DEV_DB_PASSWORD_PLACEHOLDER>';
    END IF;
END
$$;

-- データベース接続権限
\c sanbou_dev
GRANT CONNECT ON DATABASE sanbou_dev TO sanbou_app_dev;

-- スキーマ使用権限（public のみ）
GRANT USAGE ON SCHEMA public TO sanbou_app_dev;

-- CRUD 権限
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sanbou_app_dev;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO sanbou_app_dev;

-- DDL 権限（開発環境のみ：テーブル作成を許可）
GRANT CREATE ON SCHEMA public TO sanbou_app_dev;

-- 今後追加されるテーブルにも自動で権限付与
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sanbou_app_dev;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT USAGE, SELECT ON SEQUENCES TO sanbou_app_dev;

\echo '✓ 開発環境ユーザーの設定完了'
\echo ''

-- ==============================================================================
-- ステージング環境（sanbou_stg）
-- ==============================================================================

\echo '▶ ステージング環境ユーザー (sanbou_app_stg) を作成...'

-- ユーザー作成
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'sanbou_app_stg') THEN
        CREATE USER sanbou_app_stg WITH PASSWORD '<STG_DB_PASSWORD_PLACEHOLDER>';
        RAISE NOTICE 'ユーザー sanbou_app_stg を作成しました';
    ELSE
        RAISE NOTICE 'ユーザー sanbou_app_stg は既に存在します';
        -- パスワードのみ更新する場合は以下をアンコメント
        -- ALTER USER sanbou_app_stg WITH PASSWORD '<STG_DB_PASSWORD_PLACEHOLDER>';
    END IF;
END
$$;

-- データベース接続権限
\c sanbou_stg
GRANT CONNECT ON DATABASE sanbou_stg TO sanbou_app_stg;

-- スキーマ使用権限（public のみ）
GRANT USAGE ON SCHEMA public TO sanbou_app_stg;

-- CRUD 権限のみ（DDL は不可）
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sanbou_app_stg;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO sanbou_app_stg;

-- 今後追加されるテーブルにも自動で権限付与
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sanbou_app_stg;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT USAGE, SELECT ON SEQUENCES TO sanbou_app_stg;

\echo '✓ ステージング環境ユーザーの設定完了'
\echo ''

-- ==============================================================================
-- 本番環境（sanbou_prod）
-- ==============================================================================

\echo '▶ 本番環境ユーザー (sanbou_app_prod) を作成...'

-- ユーザー作成
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'sanbou_app_prod') THEN
        CREATE USER sanbou_app_prod WITH PASSWORD '<PROD_DB_PASSWORD_PLACEHOLDER>';
        RAISE NOTICE 'ユーザー sanbou_app_prod を作成しました';
    ELSE
        RAISE NOTICE 'ユーザー sanbou_app_prod は既に存在します';
        -- パスワードのみ更新する場合は以下をアンコメント
        -- ALTER USER sanbou_app_prod WITH PASSWORD '<PROD_DB_PASSWORD_PLACEHOLDER>';
    END IF;
END
$$;

-- データベース接続権限
\c sanbou_prod
GRANT CONNECT ON DATABASE sanbou_prod TO sanbou_app_prod;

-- スキーマ使用権限（public のみ）
GRANT USAGE ON SCHEMA public TO sanbou_app_prod;

-- CRUD 権限のみ（DDL は完全に禁止）
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sanbou_app_prod;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO sanbou_app_prod;

-- 今後追加されるテーブルにも自動で権限付与
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sanbou_app_prod;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT USAGE, SELECT ON SEQUENCES TO sanbou_app_prod;

\echo '✓ 本番環境ユーザーの設定完了'
\echo ''

-- ==============================================================================
-- 確認クエリ
-- ==============================================================================

\echo '=========================================='
\echo '作成されたユーザーの確認'
\echo '=========================================='

-- すべてのユーザーを表示
\du

\echo ''
\echo '=========================================='
\echo 'データベースごとの権限確認'
\echo '=========================================='

-- 各データベースの接続権限を確認
SELECT
    datname AS database,
    array_agg(DISTINCT grantee) AS allowed_users
FROM
    pg_database d
    CROSS JOIN LATERAL (
        SELECT r.rolname AS grantee
        FROM pg_roles r
        WHERE has_database_privilege(r.oid, d.oid, 'CONNECT')
        AND r.rolname LIKE 'sanbou_app_%'
    ) perms
WHERE
    datname IN ('sanbou_dev', 'sanbou_stg', 'sanbou_prod')
GROUP BY
    datname
ORDER BY
    datname;

\echo ''
\echo '=========================================='
\echo '完了'
\echo '=========================================='
\echo ''
\echo '次のステップ:'
\echo '1. secrets/.env.*.secrets ファイルに新しいパスワードを設定'
\echo '2. env/.env.* ファイルの POSTGRES_USER を環境別ユーザーに変更'
\echo '3. アプリケーションを再起動して接続確認'
\echo ''

-- ==============================================================================
-- 追加のスキーマがある場合の権限設定（オプション）
-- ==============================================================================
--
-- 【注意】
-- プロジェクトに raw / stg / mart などの追加スキーマがある場合、
-- 以下のコマンドをアンコメントして実行してください。
--
-- ■ 開発環境（すべてのスキーマに CRUD 権限）
-- \c sanbou_dev
-- GRANT USAGE ON SCHEMA raw, stg, mart TO sanbou_app_dev;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA raw TO sanbou_app_dev;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA stg TO sanbou_app_dev;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA mart TO sanbou_app_dev;
--
-- ■ ステージング環境（スキーマごとに権限を分離）
-- \c sanbou_stg
-- GRANT USAGE ON SCHEMA raw, stg, mart TO sanbou_app_stg;
-- -- raw: 書き込みのみ
-- GRANT INSERT ON ALL TABLES IN SCHEMA raw TO sanbou_app_stg;
-- -- stg: 読み書き
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA stg TO sanbou_app_stg;
-- -- mart: 読み取りのみ
-- GRANT SELECT ON ALL TABLES IN SCHEMA mart TO sanbou_app_stg;
--
-- ■ 本番環境（ステージングと同様）
-- \c sanbou_prod
-- GRANT USAGE ON SCHEMA raw, stg, mart TO sanbou_app_prod;
-- GRANT INSERT ON ALL TABLES IN SCHEMA raw TO sanbou_app_prod;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA stg TO sanbou_app_prod;
-- GRANT SELECT ON ALL TABLES IN SCHEMA mart TO sanbou_app_prod;
--
-- ==============================================================================
