-- Grant schema permissions for core_api database user
-- This script ensures myuser has access to ref and mart schemas
-- Run this after database initialization or schema migrations

-- Grant usage on schemas
GRANT USAGE ON SCHEMA ref TO myuser;
GRANT USAGE ON SCHEMA mart TO myuser;

-- Grant select on all existing tables and views
GRANT SELECT ON ALL TABLES IN SCHEMA ref TO myuser;
GRANT SELECT ON ALL TABLES IN SCHEMA mart TO myuser;

-- Grant select on future tables and views (important for new migrations)
ALTER DEFAULT PRIVILEGES IN SCHEMA ref GRANT SELECT ON TABLES TO myuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA mart GRANT SELECT ON TABLES TO myuser;

-- Grant necessary permissions for public schema (if needed)
GRANT USAGE ON SCHEMA public TO myuser;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO myuser;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO myuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO myuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO myuser;

-- Verify permissions were granted
\echo 'Permissions granted successfully'
\echo 'Verifying ref schema permissions:'
\dp ref.*
\echo 'Verifying mart schema permissions:'
\dp mart.*
