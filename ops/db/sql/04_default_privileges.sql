-- ============================================================
-- 04_default_privileges.sql - デフォルト権限設定（冪等）
-- ============================================================
-- 
-- 目的: 新規作成されるオブジェクトに対して自動的に権限を付与
-- 
-- 実行方法:
--   psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
--        -v app_user="$POSTGRES_USER" \
--        -f 04_default_privileges.sql
-- 
-- パラメータ:
--   app_user: アプリ接続ユーザー名（例: sanbou_app_dev）
-- 
-- 重要:
--   - sanbou_owner が作成する将来のオブジェクトに対して権限を自動付与
--   - マイグレーション実行後に手動で GRANT する必要がなくなる
-- ============================================================

\set ON_ERROR_STOP 0

\echo ''
\echo '================================================================'
\echo '04_default_privileges.sql - デフォルト権限設定'
\echo '================================================================'
\echo ''

-- ============================================================
-- 1. RW (Read-Write) スキーマのデフォルト権限
-- ============================================================
\echo '[1/2] RW スキーマのデフォルト権限設定'

DO $$
DECLARE
    app_user_var text := current_setting('vars.app_user', true);
    rw_schemas text[] := ARRAY[
        'raw', 'stg', 'kpi', 'log', 'app', 'app_auth', 'forecast', 'jobs', 'sandbox', 'public'
    ];
    schema_rec text;
BEGIN
    FOREACH schema_rec IN ARRAY rw_schemas
    LOOP
        IF EXISTS (SELECT FROM pg_catalog.pg_namespace WHERE nspname = schema_rec) THEN
            -- テーブル: RW 権限
            EXECUTE format(
                'ALTER DEFAULT PRIVILEGES FOR ROLE sanbou_owner IN SCHEMA %I ' ||
                'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO %I',
                schema_rec,
                app_user_var
            );
            
            -- シーケンス: USAGE, SELECT（自動採番に必須）
            EXECUTE format(
                'ALTER DEFAULT PRIVILEGES FOR ROLE sanbou_owner IN SCHEMA %I ' ||
                'GRANT USAGE, SELECT ON SEQUENCES TO %I',
                schema_rec,
                app_user_var
            );
            
            -- 関数: EXECUTE
            EXECUTE format(
                'ALTER DEFAULT PRIVILEGES FOR ROLE sanbou_owner IN SCHEMA %I ' ||
                'GRANT EXECUTE ON FUNCTIONS TO %I',
                schema_rec,
                app_user_var
            );
            
            RAISE NOTICE '✓ [RW default] %.% → %', 
                         schema_rec,
                         repeat(' ', 12 - length(schema_rec::text)),
                         app_user_var;
        END IF;
    END LOOP;
END
$$;

-- ============================================================
-- 2. RO (Read-Only) スキーマのデフォルト権限
-- ============================================================
\echo '[2/2] RO スキーマのデフォルト権限設定'

DO $$
DECLARE
    app_user_var text := current_setting('vars.app_user', true);
    ro_schemas text[] := ARRAY['mart', 'ref'];
    schema_rec text;
BEGIN
    FOREACH schema_rec IN ARRAY ro_schemas
    LOOP
        IF EXISTS (SELECT FROM pg_catalog.pg_namespace WHERE nspname = schema_rec) THEN
            -- テーブル: SELECT のみ
            EXECUTE format(
                'ALTER DEFAULT PRIVILEGES FOR ROLE sanbou_owner IN SCHEMA %I ' ||
                'GRANT SELECT ON TABLES TO %I',
                schema_rec,
                app_user_var
            );
            
            -- 関数: EXECUTE
            EXECUTE format(
                'ALTER DEFAULT PRIVILEGES FOR ROLE sanbou_owner IN SCHEMA %I ' ||
                'GRANT EXECUTE ON FUNCTIONS TO %I',
                schema_rec,
                app_user_var
            );
            
            RAISE NOTICE '✓ [RO default] %.% → %', 
                         schema_rec,
                         repeat(' ', 12 - length(schema_rec::text)),
                         app_user_var;
        END IF;
    END LOOP;
END
$$;

\echo ''
\echo '================================================================'
\echo '04_default_privileges.sql 完了'
\echo '================================================================'
\echo ''
\echo '✓ デフォルト権限設定完了:'
\echo '  - 今後 sanbou_owner が作成するオブジェクトに対して自動的に権限付与'
\echo '  - マイグレーション実行後も権限エラーなし'
\echo '  - 特に SEQUENCE 権限が自動付与されるため、serial/identity カラムの'
\echo '    INSERT が即座に動作する'
\echo ''

\set ON_ERROR_STOP 1
