-- =============================================================
-- extensions_after_restore.sql
-- 拡張機能の再有効化テンプレート
-- 必要な拡張のみ残して使用してください
-- =============================================================

-- PostGIS（地理空間データ）
CREATE EXTENSION IF NOT EXISTS postgis;

-- UUID 生成
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- トライグラム検索（全文検索の補助）
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- pgvector（ベクトル検索、AI/ML用）
-- CREATE EXTENSION IF NOT EXISTS vector;

-- その他の拡張（必要に応じてコメント解除）
-- CREATE EXTENSION IF NOT EXISTS hstore;
-- CREATE EXTENSION IF NOT EXISTS citext;
-- CREATE EXTENSION IF NOT EXISTS btree_gist;
