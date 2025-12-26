-- ============================================================
-- 03_grants.sql - 権限付与（冪等）
-- ============================================================
--
-- 目的: アプリユーザーに必要十分な権限を付与
--
-- 実行方法:
--   psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
--        -v app_user="$POSTGRES_USER" \
--        -f 03_grants.sql
--
-- パラメータ:
--   app_user: アプリ接続ユーザー名（例: sanbou_app_dev）
--
-- 権限方針:
--   - raw, stg, kpi, log, app, app_auth, forecast, jobs, sandbox, public: RW + SEQUENCES
--   - mart, ref: RO (SELECT のみ)
-- ============================================================

\set ON_ERROR_STOP 0

\echo ''
\echo '================================================================'
\echo '03_grants.sql - 権限付与'
\echo '================================================================'
\echo ''

-- ============================================================
-- 1. RW (Read-Write) スキーマへの権限付与
-- ============================================================
\echo '[1/3] RW スキーマへの権限付与'

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
            -- USAGE 権限
            EXECUTE format('GRANT USAGE ON SCHEMA %I TO %I', schema_rec, app_user_var);

            -- テーブル・ビューへの RW 権限
            EXECUTE format(
                'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA %I TO %I',
                schema_rec,
                app_user_var
            );

            -- シーケンスへの権限（自動採番に必須）
            EXECUTE format(
                'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA %I TO %I',
                schema_rec,
                app_user_var
            );

            -- 関数への EXECUTE 権限
            EXECUTE format(
                'GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA %I TO %I',
                schema_rec,
                app_user_var
            );

            RAISE NOTICE '✓ [RW] %.% → %',
                         schema_rec,
                         repeat(' ', 12 - length(schema_rec::text)),
                         app_user_var;
        ELSE
            RAISE NOTICE '  Skip %.% (schema does not exist)',
                         schema_rec,
                         repeat(' ', 12 - length(schema_rec::text));
        END IF;
    END LOOP;
END
$$;

-- ============================================================
-- 2. RO (Read-Only) スキーマへの権限付与
-- ============================================================
\echo '[2/3] RO スキーマへの権限付与'

DO $$
DECLARE
    app_user_var text := current_setting('vars.app_user', true);
    ro_schemas text[] := ARRAY['mart', 'ref'];
    schema_rec text;
BEGIN
    FOREACH schema_rec IN ARRAY ro_schemas
    LOOP
        IF EXISTS (SELECT FROM pg_catalog.pg_namespace WHERE nspname = schema_rec) THEN
            -- USAGE 権限
            EXECUTE format('GRANT USAGE ON SCHEMA %I TO %I', schema_rec, app_user_var);

            -- テーブル・ビューへの SELECT 権限のみ
            EXECUTE format(
                'GRANT SELECT ON ALL TABLES IN SCHEMA %I TO %I',
                schema_rec,
                app_user_var
            );

            -- 関数への EXECUTE 権限
            EXECUTE format(
                'GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA %I TO %I',
                schema_rec,
                app_user_var
            );

            RAISE NOTICE '✓ [RO] %.% → %',
                         schema_rec,
                         repeat(' ', 12 - length(schema_rec::text)),
                         app_user_var;
        ELSE
            RAISE NOTICE '  Skip %.% (schema does not exist)',
                         schema_rec,
                         repeat(' ', 12 - length(schema_rec::text));
        END IF;
    END LOOP;
END
$$;

-- ============================================================
-- 3. 特殊権限: マテリアライズドビューのリフレッシュ権限
-- ============================================================
\echo '[3/3] マテリアライズドビュー権限'

DO $$
DECLARE
    app_user_var text := current_setting('vars.app_user', true);
    mv_schemas text[] := ARRAY['mart', 'kpi'];
    schema_rec text;
    mv_count int := 0;
BEGIN
    FOREACH schema_rec IN ARRAY mv_schemas
    LOOP
        IF EXISTS (SELECT FROM pg_catalog.pg_namespace WHERE nspname = schema_rec) THEN
            -- マテリアライズドビューの REFRESH 権限
            -- （PostgreSQL では owner のみが REFRESH 可能だが、将来の拡張のため記載）
            EXECUTE format(
                'GRANT SELECT ON ALL TABLES IN SCHEMA %I TO %I',
                schema_rec,
                app_user_var
            );
            mv_count := mv_count + 1;
        END IF;
    END LOOP;

    IF mv_count > 0 THEN
        RAISE NOTICE '✓ Materialized views: SELECT granted in % schemas', mv_count;
        RAISE NOTICE '  Note: REFRESH requires owner privileges';
    END IF;
END
$$;

\echo ''
\echo '================================================================'
\echo '03_grants.sql 完了'
\echo '================================================================'
\echo ''
\echo '✓ 権限付与完了:'
\echo '  - RW schemas: raw, stg, kpi, log, app, app_auth, forecast, jobs, sandbox, public'
\echo '  - RO schemas: mart, ref'
\echo '  - SEQUENCES: USAGE, SELECT granted (for serial/identity columns)'
\echo ''

\set ON_ERROR_STOP 1
