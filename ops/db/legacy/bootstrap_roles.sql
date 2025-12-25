-- ============================================================
-- bootstrap_roles.sql
--
-- 目的: app_readonly ロールと基本権限の冪等セットアップ
-- 用途: Alembic マイグレーション実行前に毎回実行（冪等なので安全）
--
-- 実行方法（Makefile 経由推奨）:
--   make db-bootstrap-roles-env ENV=local_dev
--   make db-bootstrap-roles-env ENV=vm_stg
--   make db-bootstrap-roles-env ENV=vm_prod
--
-- 直接実行する場合:
--   psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=0 -f bootstrap_roles.sql
--
-- 注意:
--   - 冪等性を確保するため IF NOT EXISTS / IF EXISTS を使用
--   - スキーマやテーブルが存在しない場合でもエラーで停止しない
--   - ON_ERROR_STOP=0 で実行することを推奨（一部のGRANTが失敗しても継続）
-- ============================================================

-- ON_ERROR_STOP を無効化（エラーがあっても継続）
\set ON_ERROR_STOP 0

-- ============================================================
-- 1. app_readonly ロールの作成（冪等）
-- ============================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_readonly'
    ) THEN
        CREATE ROLE app_readonly NOLOGIN;
        RAISE NOTICE 'Created role: app_readonly';
    ELSE
        RAISE NOTICE 'Role app_readonly already exists';
    END IF;
END
$$;

-- ============================================================
-- 2. スキーマへの USAGE 権限付与（存在する場合のみ）
-- ============================================================

-- mart スキーマ
DO $$
BEGIN
    IF EXISTS (
        SELECT FROM pg_catalog.pg_namespace WHERE nspname = 'mart'
    ) THEN
        EXECUTE 'GRANT USAGE ON SCHEMA mart TO app_readonly';
        RAISE NOTICE 'Granted USAGE on schema mart to app_readonly';
    ELSE
        RAISE NOTICE 'Schema mart does not exist, skipping USAGE grant';
    END IF;
END
$$;

-- stg スキーマ
DO $$
BEGIN
    IF EXISTS (
        SELECT FROM pg_catalog.pg_namespace WHERE nspname = 'stg'
    ) THEN
        EXECUTE 'GRANT USAGE ON SCHEMA stg TO app_readonly';
        RAISE NOTICE 'Granted USAGE on schema stg to app_readonly';
    ELSE
        RAISE NOTICE 'Schema stg does not exist, skipping USAGE grant';
    END IF;
END
$$;

-- ============================================================
-- 3. テーブル・ビューへの SELECT 権限付与（存在する場合のみ）
-- ============================================================

-- mart スキーマ内の全テーブル・ビュー
DO $$
BEGIN
    IF EXISTS (
        SELECT FROM pg_catalog.pg_namespace WHERE nspname = 'mart'
    ) THEN
        EXECUTE 'GRANT SELECT ON ALL TABLES IN SCHEMA mart TO app_readonly';
        RAISE NOTICE 'Granted SELECT on all tables in mart to app_readonly';
    ELSE
        RAISE NOTICE 'Schema mart does not exist, skipping SELECT grant';
    END IF;
END
$$;

-- stg スキーマ内の全テーブル・ビュー
DO $$
BEGIN
    IF EXISTS (
        SELECT FROM pg_catalog.pg_namespace WHERE nspname = 'stg'
    ) THEN
        EXECUTE 'GRANT SELECT ON ALL TABLES IN SCHEMA stg TO app_readonly';
        RAISE NOTICE 'Granted SELECT on all tables in stg to app_readonly';
    ELSE
        RAISE NOTICE 'Schema stg does not exist, skipping SELECT grant';
    END IF;
END
$$;

-- ============================================================
-- 4. 将来作成されるテーブル・ビューへのデフォルト権限設定
-- ============================================================

-- mart スキーマ
DO $$
BEGIN
    IF EXISTS (
        SELECT FROM pg_catalog.pg_namespace WHERE nspname = 'mart'
    ) THEN
        -- デフォルト権限を付与するユーザーを取得
        EXECUTE format(
            'ALTER DEFAULT PRIVILEGES IN SCHEMA mart GRANT SELECT ON TABLES TO app_readonly'
        );
        RAISE NOTICE 'Set default privileges for future tables in mart';
    ELSE
        RAISE NOTICE 'Schema mart does not exist, skipping default privileges';
    END IF;
END
$$;

-- stg スキーマ
DO $$
BEGIN
    IF EXISTS (
        SELECT FROM pg_catalog.pg_namespace WHERE nspname = 'stg'
    ) THEN
        EXECUTE format(
            'ALTER DEFAULT PRIVILEGES IN SCHEMA stg GRANT SELECT ON TABLES TO app_readonly'
        );
        RAISE NOTICE 'Set default privileges for future tables in stg';
    ELSE
        RAISE NOTICE 'Schema stg does not exist, skipping default privileges';
    END IF;
END
$$;

-- ============================================================
-- 5. 完了メッセージ
-- ============================================================
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Bootstrap roles completed successfully';
    RAISE NOTICE '========================================';
END
$$;

-- ON_ERROR_STOP を再度有効化（元に戻す）
\set ON_ERROR_STOP 1
