-- ================================
-- DB権限設計とクリーンアップ（local_dev）
-- ================================
-- 目的: Alembic migration時の権限エラーを根絶
-- 方針: すべてのスキーマオブジェクトを sanbou_app_dev 所有に統一
-- 日付: 2025-12-19

-- ================================
-- 1. 現状の問題
-- ================================
-- - viewの所有者が混在（myuser と sanbou_app_dev）
-- - Alembic（sanbou_app_dev）が myuser 所有のviewを更新できない
-- - 権限エラー: "must be owner of view v_reserve_daily_for_forecast"

-- ================================
-- 2. 設計方針
-- ================================
-- 【ユーザー役割】
-- - sanbou_app_dev: アプリケーション専用ユーザー（DDL/DML可能、所有者）
-- - app_readonly: 読み取り専用ユーザー（将来のレポート機能用）
-- - myuser: スーパーユーザー（緊急時のみ使用、通常使用禁止）

-- 【所有権ルール】
-- - すべてのスキーマ（stg, mart, forecast等）: sanbou_app_dev 所有
-- - すべてのテーブル・ビュー・シーケンス: sanbou_app_dev 所有
-- - Alembic migrationは sanbou_app_dev で実行
-- - アプリケーションも sanbou_app_dev で接続

-- ================================
-- 3. クリーンアップ（既存オブジェクトの所有者変更）
-- ================================
-- 注意: このスクリプトは myuser（スーパーユーザー）で実行してください

-- 3-1. スキーマの所有者を統一
ALTER SCHEMA stg OWNER TO sanbou_app_dev;
ALTER SCHEMA mart OWNER TO sanbou_app_dev;
ALTER SCHEMA forecast OWNER TO sanbou_app_dev;

-- 3-2. テーブルの所有者を統一（stg）
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'stg' 
          AND tableowner != 'sanbou_app_dev'
    LOOP
        EXECUTE format('ALTER TABLE stg.%I OWNER TO sanbou_app_dev', r.tablename);
        RAISE NOTICE 'Changed owner of table stg.%', r.tablename;
    END LOOP;
END $$;

-- 3-3. テーブルの所有者を統一（mart）
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'mart' 
          AND tableowner != 'sanbou_app_dev'
    LOOP
        EXECUTE format('ALTER TABLE mart.%I OWNER TO sanbou_app_dev', r.tablename);
        RAISE NOTICE 'Changed owner of table mart.%', r.tablename;
    END LOOP;
END $$;

-- 3-4. テーブルの所有者を統一（forecast）
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'forecast' 
          AND tableowner != 'sanbou_app_dev'
    LOOP
        EXECUTE format('ALTER TABLE forecast.%I OWNER TO sanbou_app_dev', r.tablename);
        RAISE NOTICE 'Changed owner of table forecast.%', r.tablename;
    END LOOP;
END $$;

-- 3-5. ビューの所有者を統一（stg）
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT viewname 
        FROM pg_views 
        WHERE schemaname = 'stg' 
          AND viewowner != 'sanbou_app_dev'
    LOOP
        EXECUTE format('ALTER VIEW stg.%I OWNER TO sanbou_app_dev', r.viewname);
        RAISE NOTICE 'Changed owner of view stg.%', r.viewname;
    END LOOP;
END $$;

-- 3-6. ビューの所有者を統一（mart）
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT viewname 
        FROM pg_views 
        WHERE schemaname = 'mart' 
          AND viewowner != 'sanbou_app_dev'
    LOOP
        EXECUTE format('ALTER VIEW mart.%I OWNER TO sanbou_app_dev', r.viewname);
        RAISE NOTICE 'Changed owner of view mart.%', r.viewname;
    END LOOP;
END $$;

-- 3-7. シーケンスの所有者を統一
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT schemaname, sequencename
        FROM pg_sequences 
        WHERE schemaname IN ('stg', 'mart', 'forecast')
    LOOP
        EXECUTE format('ALTER SEQUENCE %I.%I OWNER TO sanbou_app_dev', 
                       r.schemaname, r.sequencename);
        RAISE NOTICE 'Changed owner of sequence %.%', r.schemaname, r.sequencename;
    END LOOP;
END $$;

-- ================================
-- 4. デフォルト権限の設定（将来作成されるオブジェクト用）
-- ================================
-- sanbou_app_dev が作成する新しいオブジェクトは自動的に sanbou_app_dev 所有になる
ALTER DEFAULT PRIVILEGES FOR ROLE sanbou_app_dev IN SCHEMA stg
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sanbou_app_dev;

ALTER DEFAULT PRIVILEGES FOR ROLE sanbou_app_dev IN SCHEMA mart
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sanbou_app_dev;

ALTER DEFAULT PRIVILEGES FOR ROLE sanbou_app_dev IN SCHEMA forecast
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sanbou_app_dev;

-- app_readonly に読み取り専用権限を付与（将来のレポート機能用）
ALTER DEFAULT PRIVILEGES FOR ROLE sanbou_app_dev IN SCHEMA stg
    GRANT SELECT ON TABLES TO app_readonly;

ALTER DEFAULT PRIVILEGES FOR ROLE sanbou_app_dev IN SCHEMA mart
    GRANT SELECT ON TABLES TO app_readonly;

ALTER DEFAULT PRIVILEGES FOR ROLE sanbou_app_dev IN SCHEMA forecast
    GRANT SELECT ON TABLES TO app_readonly;

-- ================================
-- 5. 既存オブジェクトへの読み取り権限付与
-- ================================
-- app_readonly に既存テーブル・ビューの読み取り権限を付与
GRANT USAGE ON SCHEMA stg TO app_readonly;
GRANT USAGE ON SCHEMA mart TO app_readonly;
GRANT USAGE ON SCHEMA forecast TO app_readonly;

GRANT SELECT ON ALL TABLES IN SCHEMA stg TO app_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA mart TO app_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA forecast TO app_readonly;

-- ================================
-- 6. 確認クエリ
-- ================================
-- 実行後、以下のクエリで所有者が統一されたか確認してください：

-- 6-1. テーブル所有者確認
SELECT schemaname, tablename, tableowner
FROM pg_tables
WHERE schemaname IN ('stg', 'mart', 'forecast')
ORDER BY schemaname, tablename;

-- 6-2. ビュー所有者確認
SELECT schemaname, viewname, viewowner
FROM pg_views
WHERE schemaname IN ('stg', 'mart', 'forecast')
ORDER BY schemaname, viewname;

-- 6-3. スキーマ所有者確認
SELECT nspname AS schema_name, pg_get_userbyid(nspowner) AS schema_owner
FROM pg_namespace
WHERE nspname IN ('stg', 'mart', 'forecast')
ORDER BY nspname;

-- ================================
-- 7. 期待される結果
-- ================================
-- すべてのオブジェクトの tableowner/viewowner/schema_owner が sanbou_app_dev になること
-- これにより Alembic migration時の権限エラーが解消されます
