SELECT current_database();

-- ==========================
-- 基本ロール（グループロール）
-- ==========================
CREATE ROLE app_read  NOLOGIN;
CREATE ROLE app_write NOLOGIN;
CREATE ROLE app_admin NOLOGIN;


--権限確認
SELECT rolname, rolsuper, rolcanlogin
FROM pg_roles
ORDER BY rolname;

SELECT schema_name