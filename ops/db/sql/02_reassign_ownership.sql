-- ============================================================
-- 02_reassign_ownership.sql - 所有権移管（冪等）
-- ============================================================
-- 
-- 目的: すべてのDBオブジェクトの所有者を sanbou_owner に統一
-- 
-- 実行方法:
--   psql -U myuser -d sanbou_dev \
--        -c "SET vars.app_user TO 'sanbou_app_dev'" \
--        -f 02_reassign_ownership.sql
-- 
-- パラメータ:
--   vars.app_user: 現在の所有者（例: sanbou_app_dev）
-- ============================================================

\set ON_ERROR_STOP 0

\echo ''
\echo '================================================================'
\echo '02_reassign_ownership.sql - 所有権移管'
\echo '================================================================'
\echo ''

-- ============================================================
-- 1. public スキーマの所有権を myuser → sanbou_owner へ
-- ============================================================
\echo '[1/3] public スキーマ所有権の移管'

DO $$
BEGIN
    -- public スキーマの所有者が myuser の場合のみ変更
    IF (SELECT pg_catalog.pg_get_userbyid(nspowner) FROM pg_namespace WHERE nspname = 'public') = 'myuser' THEN
        ALTER SCHEMA public OWNER TO sanbou_owner;
        RAISE NOTICE '✓ Changed public schema owner: myuser → sanbou_owner';
    ELSE
        RAISE NOTICE '✓ public schema is not owned by myuser, skipping';
    END IF;
END
$$;

\echo ''

-- ============================================================
-- 2. アプリケーションスキーマの所有権を確認・移管
-- ============================================================
\echo '[2/3] アプリケーションスキーマ所有権の移管'

DO $$
DECLARE
    app_user_input text := current_setting('vars.app_user', true);
    schema_list text[] := ARRAY[
        'raw', 'stg', 'mart', 'ref', 'kpi', 'log', 
        'app', 'app_auth', 'forecast', 'jobs', 'sandbox'
    ];
    schema_name text;
    current_owner text;
BEGIN
    IF app_user_input IS NULL THEN
        RAISE EXCEPTION 'Missing vars.app_user setting';
    END IF;
    
    RAISE NOTICE 'Application User: %', app_user_input;
    
    FOREACH schema_name IN ARRAY schema_list
    LOOP
        -- スキーマの存在確認
        IF EXISTS (
            SELECT FROM pg_catalog.pg_namespace WHERE nspname = schema_name
        ) THEN
            -- 現在の owner 取得
            SELECT pg_catalog.pg_get_userbyid(nspowner)
            INTO current_owner
            FROM pg_namespace
            WHERE nspname = schema_name;
            
            -- owner が sanbou_owner でない場合のみ変更
            IF current_owner != 'sanbou_owner' THEN
                EXECUTE format('ALTER SCHEMA %I OWNER TO sanbou_owner', schema_name);
                RAISE NOTICE '✓ Changed schema % owner: % → sanbou_owner', 
                             schema_name, current_owner;
            ELSE
                RAISE NOTICE '  Schema % already owned by sanbou_owner', schema_name;
            END IF;
        ELSE
            RAISE NOTICE '  Schema % does not exist, skipping', schema_name;
        END IF;
    END LOOP;
END
$$;

\echo ''

-- ============================================================
-- 3. アプリユーザーが所有するテーブル・シーケンスを sanbou_owner に移管
-- ============================================================
\echo '[3/3] テーブル・シーケンス所有権の移管'

DO $$
DECLARE
    app_user_input text := current_setting('vars.app_user', true);
    schema_list text[] := ARRAY[
        'raw', 'stg', 'mart', 'ref', 'kpi', 'log', 
        'app', 'app_auth', 'forecast', 'jobs', 'sandbox', 'public'
    ];
    schema_rec text;
    table_count int;
    sequence_count int;
    table_name text;
    seq_name text;
BEGIN
    IF app_user_input IS NULL THEN
        RAISE EXCEPTION 'Missing vars.app_user setting';
    END IF;
    
    FOREACH schema_rec IN ARRAY schema_list
    LOOP
        -- スキーマが存在する場合のみ処理
        IF EXISTS (
            SELECT FROM pg_catalog.pg_namespace WHERE nspname = schema_rec
        ) THEN
            -- テーブルの所有権移管（app_user が所有しているもののみ）
            SELECT COUNT(*)
            INTO table_count
            FROM pg_tables
            WHERE schemaname = schema_rec
              AND tableowner = app_user_input;
            
            IF table_count > 0 THEN
                FOR table_name IN 
                    SELECT tablename 
                    FROM pg_tables 
                    WHERE schemaname = schema_rec 
                      AND tableowner = app_user_input
                LOOP
                    EXECUTE format('ALTER TABLE %I.%I OWNER TO sanbou_owner', 
                                   schema_rec, table_name);
                END LOOP;
                RAISE NOTICE '✓ Reassigned % tables in schema %', table_count, schema_rec;
            END IF;
            
            -- シーケンスの所有権移管
            SELECT COUNT(*)
            INTO sequence_count
            FROM pg_sequences
            WHERE schemaname = schema_rec
              AND sequenceowner = app_user_input;
            
            IF sequence_count > 0 THEN
                FOR seq_name IN 
                    SELECT sequencename 
                    FROM pg_sequences 
                    WHERE schemaname = schema_rec 
                      AND sequenceowner = app_user_input
                LOOP
                    EXECUTE format('ALTER SEQUENCE %I.%I OWNER TO sanbou_owner', 
                                   schema_rec, seq_name);
                END LOOP;
                RAISE NOTICE '✓ Reassigned % sequences in schema %', sequence_count, schema_rec;
            END IF;
        END IF;
    END LOOP;
    
    RAISE NOTICE '✓ Ownership reassignment completed';
END
$$;

\echo ''
\echo '================================================================'
\echo '02_reassign_ownership.sql 完了'
\echo '================================================================'
\echo ''

\set ON_ERROR_STOP 1
