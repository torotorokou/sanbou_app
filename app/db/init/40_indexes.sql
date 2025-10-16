
-- SET search_path = app, public;

-- CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username);
-- CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- CREATE INDEX IF NOT EXISTS idx_items_name_trgm ON items USING gin (name gin_trgm_ops);

-- CREATE INDEX IF NOT EXISTS idx_items_owner_id ON items(owner_id);
-- -- 40_indexes.sql
-- -- 説明: インデックス作成はこのファイルでは行いません。安全のためコメントのみ。

-- /* no-op: intentionally empty to avoid side-effects when run in CI or init steps */
