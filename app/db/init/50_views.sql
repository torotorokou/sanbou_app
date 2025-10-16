
-- SET search_path = app, public;

-- CREATE OR REPLACE VIEW v_active_users_with_item_count AS
-- SELECT u.id, u.username, u.email, u.is_active, COUNT(i.*) AS item_count
-- FROM users u
-- LEFT JOIN items i ON i.owner_id = u.id
-- WHERE u.is_active = true
-- GROUP BY u.id;

-- -- 50_views.sql
-- -- 説明: ビュー定義はこのファイルでは行いません。安全のため no-op。

-- /* no-op: intentionally empty to avoid side-effects when run in CI or init steps */
