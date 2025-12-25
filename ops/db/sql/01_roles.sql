-- ============================================================
-- 01_roles.sql - ロール作成（冪等）
-- ============================================================
--
-- 目的: sanbou_owner ロールを作成し、環境に応じた設定を行う
--
-- 実行方法:
--   psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
--        -v app_user="$POSTGRES_USER" \
--        -v env="local_dev" \
--        -f 01_roles.sql
--
-- パラメータ:
--   app_user: アプリ接続ユーザー名（例: sanbou_app_dev）
--   env: 環境名（local_dev/vm_stg/vm_prod）
-- ============================================================

\set ON_ERROR_STOP 0

\echo ''
\echo '================================================================'
\echo '01_roles.sql - ロール作成'
\echo '================================================================'
\echo ''

-- ============================================================
-- 1. sanbou_owner ロール作成（冪等）
-- ============================================================
\echo '[1/2] sanbou_owner ロール作成'

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_catalog.pg_roles WHERE rolname = 'sanbou_owner'
    ) THEN
        CREATE ROLE sanbou_owner NOLOGIN;
        RAISE NOTICE '✓ Created role: sanbou_owner (NOLOGIN)';
    ELSE
        RAISE NOTICE '✓ Role sanbou_owner already exists';
    END IF;
END
$$;

-- ============================================================
-- 2. local_dev のみ: アプリユーザーに owner ロールを付与（利便性）
-- ============================================================
\echo '[2/2] 環境別設定'

-- psql 変数を current_setting() で取得
-- （Makefile から -v app_user=xxx -v env=xxx で渡される）
DO $do$
DECLARE
    app_user_input text := current_setting('vars.app_user', true);
    env_input text := current_setting('vars.env', true);
    already_member boolean;
BEGIN
    -- NULL チェック（変数が設定されていない場合）
    IF app_user_input IS NULL OR env_input IS NULL THEN
        RAISE EXCEPTION 'Missing required variables: app_user=%, env=%',
                        app_user_input, env_input;
    END IF;

    RAISE NOTICE 'Environment: %, Application User: %', env_input, app_user_input;

    -- local_dev の場合のみ GRANT
    IF env_input = 'local_dev' THEN
        -- 既にメンバーか確認
        SELECT EXISTS(
            SELECT 1 FROM pg_auth_members m
            JOIN pg_roles r ON m.roleid = r.oid
            JOIN pg_roles u ON m.member = u.oid
            WHERE r.rolname = 'sanbou_owner'
              AND u.rolname = app_user_input
        ) INTO already_member;

        IF NOT already_member THEN
            EXECUTE format('GRANT sanbou_owner TO %I', app_user_input);
            RAISE NOTICE '✓ (local_dev only) Granted sanbou_owner to %', app_user_input;
            RAISE NOTICE '  → This allows direct migration execution in development';
        ELSE
            RAISE NOTICE '✓ (local_dev) % already has sanbou_owner role', app_user_input;
        END IF;
    ELSE
        RAISE NOTICE '✓ (%) Skipping sanbou_owner grant (not local_dev)', env_input;
        RAISE NOTICE '  → For stg/prod, use dedicated migrator user or temporary GRANT';
    END IF;
END
$do$;

\echo ''
\echo '================================================================'
\echo '01_roles.sql 完了'
\echo '================================================================'
\echo ''

\set ON_ERROR_STOP 1
