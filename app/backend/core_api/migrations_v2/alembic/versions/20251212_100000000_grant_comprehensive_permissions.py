"""grant comprehensive permissions to environment-specific app user

Revision ID: 20251212_100000000
Revises: 0001_baseline
Create Date: 2025-12-12

Purpose:
  Grant comprehensive permissions to the current environment's database user ONLY.
  This ensures proper security isolation between environments.

Target User:
  - Determined by POSTGRES_USER environment variable
  - local_dev: myuser or sanbou_app_dev
  - vm_stg: sanbou_app_stg
  - vm_prod: sanbou_app_prod

Permissions Granted:
  - USAGE on all schemas (stg, mart, ref, kpi, tmp)
  - SELECT, INSERT, UPDATE, DELETE on all tables
  - USAGE, SELECT on all sequences
  - SELECT on all views (including materialized views)
  - Special: Full permissions on materialized views for REFRESH operations

Security:
  - Each environment only grants permissions to its own user
  - Prevents cross-environment permission leakage
  - vm_stg user cannot access vm_prod, and vice versa
"""
from alembic import op
import sqlalchemy as sa
import os


# revision identifiers, used by Alembic.
revision = '20251212_100000000'
down_revision = '0001_baseline'
branch_labels = None
depends_on = None


def upgrade():
    """
    Grant comprehensive permissions to the current environment's user ONLY
    """
    # Get the current environment's database user from DB_USER or POSTGRES_USER env var
    # Prioritize DB_USER, fall back to POSTGRES_USER for backward compatibility
    current_user = os.environ.get('DB_USER') or os.environ.get('POSTGRES_USER')
    if not current_user:
        raise ValueError(
            "Database user not specified. Please set DB_USER or POSTGRES_USER environment variable.\n"
            "Example: DB_USER=sanbou_app_dev or POSTGRES_USER=sanbou_app_dev"
        )
    
    print(f"[PERMISSIONS] Environment-specific permission grant")
    print(f"[PERMISSIONS] Target user: {current_user}")
    print(f"[PERMISSIONS] Security: Only {current_user} will receive permissions (environment isolation)")
    
    # List of schemas to grant permissions on
    schemas = ['stg', 'mart', 'ref', 'kpi', 'tmp']
    
    user = current_user
    
    # Check if user exists
    check_user_sql = f"""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{user}') THEN
                RAISE NOTICE 'User {user} exists, granting permissions...';
            ELSE
                RAISE WARNING 'User {user} does not exist! Cannot grant permissions.';
                RAISE EXCEPTION 'Target user % does not exist in database', '{user}';
            END IF;
        END $$;
    """
    op.execute(check_user_sql)
    
    print(f"[PERMISSIONS] Processing user: {user}")
    
    # Grant permissions only if user exists and schema exists
    # Using DO block to handle non-existent schemas gracefully
    for schema in schemas:
        grant_sql = f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{user}') THEN
                    IF EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = '{schema}') THEN
                        -- Grant USAGE on schema
                        EXECUTE 'GRANT USAGE ON SCHEMA {schema} TO {user}';
                        
                        -- Grant ALL privileges on all tables in schema
                        EXECUTE 'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {schema} TO {user}';
                        
                        -- Grant ALL privileges on all sequences in schema
                        EXECUTE 'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {schema} TO {user}';
                        
                        -- Grant default privileges for future tables
                        EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {user}';
                        
                        -- Grant default privileges for future sequences
                        EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT USAGE, SELECT ON SEQUENCES TO {user}';
                        
                        RAISE NOTICE 'Granted permissions on schema {schema} to {user}';
                    ELSE
                        RAISE NOTICE 'Schema {schema} does not exist, skipping...';
                    END IF;
                END IF;
            END $$;
        """
        op.execute(grant_sql)
    
    # Special handling for materialized views
    # Materialized views require explicit ownership or ALL privileges to REFRESH
    grant_mv_sql = f"""
        DO $$
        DECLARE
            mv_record RECORD;
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{user}') THEN
                -- Grant ALL privileges on all materialized views
                FOR mv_record IN 
                    SELECT schemaname, matviewname 
                    FROM pg_matviews 
                    WHERE schemaname IN ('stg', 'mart', 'ref', 'kpi', 'tmp')
                LOOP
                    BEGIN
                        EXECUTE format('GRANT ALL ON %I.%I TO {user}', 
                                     mv_record.schemaname, 
                                     mv_record.matviewname);
                        RAISE NOTICE 'Granted ALL on materialized view %.% to {user}', 
                                   mv_record.schemaname, mv_record.matviewname;
                    EXCEPTION WHEN OTHERS THEN
                        RAISE WARNING 'Failed to grant on %.%: %', 
                                    mv_record.schemaname, mv_record.matviewname, SQLERRM;
                    END;
                END LOOP;
            END IF;
        END $$;
    """
    op.execute(grant_mv_sql)
    
    # Verify permissions on critical materialized views for the current environment user
    print("[PERMISSIONS] Verifying permissions on critical materialized views...")
    
    verify_sql = f"""
        SELECT 
            schemaname,
            matviewname,
            has_table_privilege('{current_user}', schemaname||'.'||matviewname, 'SELECT') as has_select,
            has_table_privilege('{current_user}', schemaname||'.'||matviewname, 'INSERT') as has_insert,
            has_table_privilege('{current_user}', schemaname||'.'||matviewname, 'UPDATE') as has_update,
            has_table_privilege('{current_user}', schemaname||'.'||matviewname, 'DELETE') as has_delete
        FROM pg_matviews
        WHERE schemaname = 'mart' 
          AND matviewname IN ('mv_receive_daily', 'mv_target_card_per_day')
        ORDER BY matviewname;
    """
    result = op.get_bind().execute(sa.text(verify_sql))
    
    print(f"\n[PERMISSIONS] Materialized View Permissions for {current_user}:")
    print("Schema | MV Name                  | SELECT | INSERT | UPDATE | DELETE")
    print("-------|--------------------------|--------|--------|--------|--------")
    for row in result:
        print(f"{row[0]:6} | {row[1]:24} | {str(row[2]):6} | {str(row[3]):6} | {str(row[4]):6} | {str(row[5]):6}")
    
    print(f"\n✅ [PERMISSIONS] Comprehensive permissions granted successfully")
    print(f"   Environment user: {current_user}")
    print(f"   Schemas: stg, mart, ref, kpi, tmp")
    print(f"   Permissions: Full CRUD + Materialized View REFRESH")
    print(f"   Security: Environment isolation maintained (only {current_user} has access)")


def downgrade():
    """
    Revoke comprehensive permissions from the current environment's user
    
    Note: This is a partial downgrade as we cannot fully revert to unknown previous state.
    We revoke the granted permissions but don't restore any previous specific grants.
    """
    # Get the current environment's database user from DB_USER or POSTGRES_USER env var
    current_user = os.environ.get('DB_USER') or os.environ.get('POSTGRES_USER')
    if not current_user:
        raise ValueError(
            "Database user not specified. Please set DB_USER or POSTGRES_USER environment variable."
        )
    
    print(f"[PERMISSIONS] Revoking comprehensive permissions from environment user: {current_user}")
    
    schemas = ['stg', 'mart', 'ref', 'kpi', 'tmp']
    
    user = current_user
    print(f"[PERMISSIONS] Revoking from user: {user}")
    
    for schema in schemas:
        revoke_sql = f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{user}') THEN
                    -- Revoke privileges on all tables
                    EXECUTE 'REVOKE SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {schema} FROM {user}';
                    
                    -- Revoke privileges on all sequences
                    EXECUTE 'REVOKE USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {schema} FROM {user}';
                    
                    -- Revoke USAGE on schema (be careful, this might affect other operations)
                    -- EXECUTE 'REVOKE USAGE ON SCHEMA {schema} FROM {user}';
                    
                    RAISE NOTICE 'Revoked permissions on schema {schema} from {user}';
                END IF;
            END $$;
        """
        op.execute(revoke_sql)
    
    # Revoke from materialized views
    revoke_mv_sql = f"""
        DO $$
        DECLARE
            mv_record RECORD;
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{user}') THEN
                FOR mv_record IN 
                    SELECT schemaname, matviewname 
                    FROM pg_matviews 
                    WHERE schemaname IN ('stg', 'mart', 'ref', 'kpi', 'tmp')
                LOOP
                    BEGIN
                        EXECUTE format('REVOKE ALL ON %I.%I FROM {user}', 
                                     mv_record.schemaname, 
                                     mv_record.matviewname);
                    EXCEPTION WHEN OTHERS THEN
                        RAISE WARNING 'Failed to revoke from %.%: %', 
                                    mv_record.schemaname, mv_record.matviewname, SQLERRM;
                    END;
                END LOOP;
            END IF;
        END $$;
    """
    op.execute(revoke_mv_sql)
    
    print(f"✅ [PERMISSIONS] Permissions revoked from {current_user}")
