
-- SET search_path = app, public;

-- CREATE OR REPLACE FUNCTION app.set_created_at()
-- RETURNS trigger LANGUAGE plpgsql AS $$
-- BEGIN
--   IF NEW.created_at IS NULL THEN
--     NEW.created_at := now();
--   END IF;
--   RETURN NEW;
-- END;
-- $$;

-- CREATE TRIGGER trg_set_created_at
-- BEFORE INSERT ON items
-- FOR EACH ROW
-- EXECUTE FUNCTION app.set_created_at();

-- CREATE TABLE IF NOT EXISTS audit_logs (
--   id BIGSERIAL PRIMARY KEY,
--   created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
--   table_name TEXT,
--   operation TEXT,
--   row_data JSONB
-- );

-- CREATE OR REPLACE FUNCTION app.log_item_changes()
-- RETURNS trigger LANGUAGE plpgsql AS $$
-- BEGIN
--   IF TG_OP = 'INSERT' THEN
--     INSERT INTO audit_logs(table_name, operation, row_data)
--     VALUES (TG_TABLE_NAME, TG_OP, row_to_json(NEW)::jsonb);
--     RETURN NEW;
--   ELSIF TG_OP = 'UPDATE' THEN
--     INSERT INTO audit_logs(table_name, operation, row_data)
--     VALUES (TG_TABLE_NAME, TG_OP, row_to_json(NEW)::jsonb);
--     RETURN NEW;
--   ELSIF TG_OP = 'DELETE' THEN
--     INSERT INTO audit_logs(table_name, operation, row_data)
--     VALUES (TG_TABLE_NAME, TG_OP, row_to_json(OLD)::jsonb);
--     RETURN OLD;
--   END IF;
--   RETURN NULL;
-- END;
-- $$;

-- CREATE TRIGGER trg_audit_items
-- AFTER INSERT OR UPDATE OR DELETE ON items
-- FOR EACH ROW
-- EXECUTE FUNCTION app.log_item_changes();
-- -- 60_functions.sql
-- -- 説明: 関数やトリガーの作成はこのファイルでは行いません。安全のため no-op。

-- /* no-op: intentionally empty to avoid side-effects when run in CI or init steps */
