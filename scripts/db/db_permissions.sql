-- =============================================================================
-- Database Roles and Permissions (Minimal Privilege)
-- =============================================================================
-- Run this script as a superuser (postgres) to create roles with minimal privileges.
--
-- Roles:
-- - core_api_user: Read/Write access to core and jobs schemas
-- - forecast_user: Read-only access to jobs/core, Read/Write access to forecast
--
-- TODO: Update passwords before running in production!
-- Usage: psql -U postgres -d your_database -f db_permissions.sql
-- =============================================================================

-- =============================================================================
-- 1. Create Roles
-- =============================================================================

DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'core_api_user') THEN
    CREATE ROLE core_api_user LOGIN PASSWORD 'CHANGE_ME_CORE_API_PASSWORD';
  END IF;
  
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'forecast_user') THEN
    CREATE ROLE forecast_user LOGIN PASSWORD 'CHANGE_ME_FORECAST_PASSWORD';
  END IF;
END
$$;

-- =============================================================================
-- 2. Grant Schema Usage
-- =============================================================================

-- core_api_user: can use core, jobs, forecast schemas
GRANT USAGE ON SCHEMA core TO core_api_user;
GRANT USAGE ON SCHEMA jobs TO core_api_user;
GRANT USAGE ON SCHEMA forecast TO core_api_user;

-- forecast_user: can use forecast, core, jobs schemas
GRANT USAGE ON SCHEMA forecast TO forecast_user;
GRANT USAGE ON SCHEMA core TO forecast_user;
GRANT USAGE ON SCHEMA jobs TO forecast_user;

-- =============================================================================
-- 3. Grant Table Permissions
-- =============================================================================

-- core_api_user: Read/Write to core and jobs, Read to forecast
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA core TO core_api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA jobs TO core_api_user;
GRANT SELECT ON ALL TABLES IN SCHEMA forecast TO core_api_user;

-- forecast_user: Read-only to jobs/core, Read/Write to forecast
GRANT SELECT ON ALL TABLES IN SCHEMA core TO forecast_user;
GRANT SELECT, UPDATE ON ALL TABLES IN SCHEMA jobs TO forecast_user;  -- UPDATE for job status
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA forecast TO forecast_user;

-- =============================================================================
-- 4. Grant Sequence Usage (for auto-increment IDs)
-- =============================================================================

GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA core TO core_api_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA jobs TO core_api_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA forecast TO forecast_user;

-- =============================================================================
-- 5. Set Default Privileges for Future Tables
-- =============================================================================

-- core_api_user: future tables in core and jobs
ALTER DEFAULT PRIVILEGES IN SCHEMA core 
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO core_api_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA jobs 
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO core_api_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA forecast 
  GRANT SELECT ON TABLES TO core_api_user;

-- forecast_user: future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA forecast 
  GRANT SELECT, INSERT, UPDATE ON TABLES TO forecast_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA core 
  GRANT SELECT ON TABLES TO forecast_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA jobs 
  GRANT SELECT, UPDATE ON TABLES TO forecast_user;

-- =============================================================================
-- 6. Grant Sequence Privileges for Future Sequences
-- =============================================================================

ALTER DEFAULT PRIVILEGES IN SCHEMA core 
  GRANT USAGE, SELECT ON SEQUENCES TO core_api_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA jobs 
  GRANT USAGE, SELECT ON SEQUENCES TO core_api_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA forecast 
  GRANT USAGE, SELECT ON SEQUENCES TO forecast_user;

-- =============================================================================
-- 7. Grant CONNECT Privilege
-- =============================================================================

GRANT CONNECT ON DATABASE current_database() TO core_api_user;
GRANT CONNECT ON DATABASE current_database() TO forecast_user;

-- =============================================================================
-- 8. Verification Queries
-- =============================================================================

-- Uncomment to verify roles and permissions:

-- \du core_api_user
-- \du forecast_user

-- SELECT grantee, table_schema, table_name, privilege_type
-- FROM information_schema.table_privileges
-- WHERE grantee IN ('core_api_user', 'forecast_user')
-- ORDER BY grantee, table_schema, table_name;

-- =============================================================================
-- Notes:
-- - core_api_user: Main API that creates jobs and inserts data
-- - forecast_user: Worker that executes jobs and writes predictions
-- - Both roles have minimal required privileges
-- - Remember to update passwords in production!
-- - Consider using connection pooling (PgBouncer) for better performance
-- =============================================================================
