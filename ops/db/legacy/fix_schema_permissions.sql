-- =============================================================================
-- Fix Schema Permissions for sanbou_app_dev user
-- =============================================================================
-- This script grants necessary permissions to sanbou_app_dev user
-- for all schemas used by the application
--
-- Run as: psql -U myuser -d sanbou_dev -f fix_schema_permissions.sql
-- =============================================================================

-- Grant USAGE on all schemas to sanbou_app_dev
GRANT USAGE ON SCHEMA app_auth TO sanbou_app_dev;
GRANT USAGE ON SCHEMA forecast TO sanbou_app_dev;
GRANT USAGE ON SCHEMA kpi TO sanbou_app_dev;
GRANT USAGE ON SCHEMA log TO sanbou_app_dev;
GRANT USAGE ON SCHEMA mart TO sanbou_app_dev;
GRANT USAGE ON SCHEMA raw TO sanbou_app_dev;
GRANT USAGE ON SCHEMA ref TO sanbou_app_dev;
GRANT USAGE ON SCHEMA sandbox TO sanbou_app_dev;
GRANT USAGE ON SCHEMA stg TO sanbou_app_dev;
GRANT USAGE ON SCHEMA public TO sanbou_app_dev;

-- Grant SELECT on all tables in each schema (read access)
GRANT SELECT ON ALL TABLES IN SCHEMA app_auth TO sanbou_app_dev;
GRANT SELECT ON ALL TABLES IN SCHEMA forecast TO sanbou_app_dev;
GRANT SELECT ON ALL TABLES IN SCHEMA kpi TO sanbou_app_dev;
GRANT SELECT ON ALL TABLES IN SCHEMA log TO sanbou_app_dev;
GRANT SELECT ON ALL TABLES IN SCHEMA mart TO sanbou_app_dev;
GRANT SELECT ON ALL TABLES IN SCHEMA raw TO sanbou_app_dev;
GRANT SELECT ON ALL TABLES IN SCHEMA ref TO sanbou_app_dev;
GRANT SELECT ON ALL TABLES IN SCHEMA sandbox TO sanbou_app_dev;
GRANT SELECT ON ALL TABLES IN SCHEMA stg TO sanbou_app_dev;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO sanbou_app_dev;

-- Grant write access to writable schemas (raw, stg, log, sandbox)
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA raw TO sanbou_app_dev;
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA stg TO sanbou_app_dev;
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA log TO sanbou_app_dev;
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA sandbox TO sanbou_app_dev;
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sanbou_app_dev;

-- Grant access to all sequences
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA app_auth TO sanbou_app_dev;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA forecast TO sanbou_app_dev;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA kpi TO sanbou_app_dev;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA log TO sanbou_app_dev;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA mart TO sanbou_app_dev;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA raw TO sanbou_app_dev;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA ref TO sanbou_app_dev;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA sandbox TO sanbou_app_dev;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA stg TO sanbou_app_dev;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO sanbou_app_dev;

-- Set default privileges for future objects created by myuser
ALTER DEFAULT PRIVILEGES FOR ROLE myuser IN SCHEMA app_auth
  GRANT SELECT ON TABLES TO sanbou_app_dev;
ALTER DEFAULT PRIVILEGES FOR ROLE myuser IN SCHEMA forecast
  GRANT SELECT ON TABLES TO sanbou_app_dev;
ALTER DEFAULT PRIVILEGES FOR ROLE myuser IN SCHEMA kpi
  GRANT SELECT ON TABLES TO sanbou_app_dev;
ALTER DEFAULT PRIVILEGES FOR ROLE myuser IN SCHEMA log
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sanbou_app_dev;
ALTER DEFAULT PRIVILEGES FOR ROLE myuser IN SCHEMA mart
  GRANT SELECT ON TABLES TO sanbou_app_dev;
ALTER DEFAULT PRIVILEGES FOR ROLE myuser IN SCHEMA raw
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sanbou_app_dev;
ALTER DEFAULT PRIVILEGES FOR ROLE myuser IN SCHEMA ref
  GRANT SELECT ON TABLES TO sanbou_app_dev;
ALTER DEFAULT PRIVILEGES FOR ROLE myuser IN SCHEMA sandbox
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sanbou_app_dev;
ALTER DEFAULT PRIVILEGES FOR ROLE myuser IN SCHEMA stg
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sanbou_app_dev;
ALTER DEFAULT PRIVILEGES FOR ROLE myuser IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sanbou_app_dev;

-- Set default privileges for sequences
ALTER DEFAULT PRIVILEGES FOR ROLE myuser IN SCHEMA app_auth
  GRANT USAGE, SELECT ON SEQUENCES TO sanbou_app_dev;
ALTER DEFAULT PRIVILEGES FOR ROLE myuser IN SCHEMA forecast
  GRANT USAGE, SELECT ON SEQUENCES TO sanbou_app_dev;
ALTER DEFAULT PRIVILEGES FOR ROLE myuser IN SCHEMA kpi
  GRANT USAGE, SELECT ON SEQUENCES TO sanbou_app_dev;
ALTER DEFAULT PRIVILEGES FOR ROLE myuser IN SCHEMA log
  GRANT USAGE, SELECT ON SEQUENCES TO sanbou_app_dev;
ALTER DEFAULT PRIVILEGES FOR ROLE myuser IN SCHEMA mart
  GRANT USAGE, SELECT ON SEQUENCES TO sanbou_app_dev;
ALTER DEFAULT PRIVILEGES FOR ROLE myuser IN SCHEMA raw
  GRANT USAGE, SELECT ON SEQUENCES TO sanbou_app_dev;
ALTER DEFAULT PRIVILEGES FOR ROLE myuser IN SCHEMA ref
  GRANT USAGE, SELECT ON SEQUENCES TO sanbou_app_dev;
ALTER DEFAULT PRIVILEGES FOR ROLE myuser IN SCHEMA sandbox
  GRANT USAGE, SELECT ON SEQUENCES TO sanbou_app_dev;
ALTER DEFAULT PRIVILEGES FOR ROLE myuser IN SCHEMA stg
  GRANT USAGE, SELECT ON SEQUENCES TO sanbou_app_dev;
ALTER DEFAULT PRIVILEGES FOR ROLE myuser IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO sanbou_app_dev;

-- Grant access to views (explicitly grant SELECT on all views)
GRANT SELECT ON ALL TABLES IN SCHEMA mart TO sanbou_app_dev;
GRANT SELECT ON ALL TABLES IN SCHEMA ref TO sanbou_app_dev;

-- Verification: Show granted privileges
\echo '=== Verification: Schema privileges for sanbou_app_dev ==='
SELECT
    nspname AS schema_name,
    has_schema_privilege('sanbou_app_dev', nspname, 'USAGE') AS has_usage
FROM pg_namespace
WHERE nspname IN ('app_auth', 'forecast', 'kpi', 'log', 'mart', 'raw', 'ref', 'sandbox', 'stg', 'public')
ORDER BY nspname;

\echo '=== Verification: Table privileges in ref schema ==='
SELECT
    schemaname,
    tablename,
    has_table_privilege('sanbou_app_dev', schemaname||'.'||tablename, 'SELECT') AS can_select
FROM pg_tables
WHERE schemaname = 'ref'
LIMIT 10;

\echo '=== Schema permissions fix completed ==='
