"""grant comprehensive permissions to all app users

Revision ID: 20251212_100000000
Revises: 0001_baseline
Create Date: 2025-12-12

Purpose:
  Grant comprehensive permissions to all application database users
  to prevent permission errors across all environments (local_dev, vm_stg, vm_prod).

Target Users:
  - myuser (legacy, for backward compatibility)
  - sanbou_app_dev (local_dev recommended user)
  - sanbou_app_stg (vm_stg recommended user)
  - sanbou_app_prod (vm_prod recommended user)

Permissions Granted:
  - USAGE on all schemas (stg, mart, ref, kpi, tmp)
  - SELECT, INSERT, UPDATE, DELETE on all tables
  - USAGE, SELECT on all sequences
  - SELECT on all views (including materialized views)
  - Special: Full permissions on materialized views for REFRESH operations

This ensures:
  - CSV upload operations work without permission errors
  - Materialized view refresh operations succeed
  - All CRUD operations on tables work correctly
  - Works consistently across all environments
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251212_100000000'
down_revision = '0001_baseline'
branch_labels = None
depends_on = None


def upgrade():
    """
    Grant comprehensive permissions to all application users
    """
    print("[PERMISSIONS] Granting comprehensive permissions to all app users...")
    
    # List of application users
    # Note: Some users may not exist in certain environments, but GRANT will silently skip them
    app_users = [
        'myuser',           # Legacy user (local_dev current)
        'sanbou_app_dev',   # Recommended user for local_dev
        'sanbou_app_stg',   # Recommended user for vm_stg
        'sanbou_app_prod',  # Recommended user for vm_prod
    ]
    
    # List of schemas to grant permissions on
    schemas = ['stg', 'mart', 'ref', 'kpi', 'tmp']
    
    for user in app_users:
        print(f"[PERMISSIONS] Processing user: {user}")
        
        # Check if user exists
        check_user_sql = f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{user}') THEN
                    RAISE NOTICE 'User {user} exists, granting permissions...';
                ELSE
                    RAISE NOTICE 'User {user} does not exist, skipping...';
                END IF;
            END $$;
        """
        op.execute(check_user_sql)
        
        # Grant permissions only if user exists and schema exists
        # Using DO block to handle non-existent users/schemas gracefully
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
    
    # Verify permissions on critical materialized views
    print("[PERMISSIONS] Verifying permissions on critical materialized views...")
    verify_sql = """
        SELECT 
            schemaname,
            matviewname,
            has_table_privilege('myuser', schemaname||'.'||matviewname, 'SELECT') as myuser_select,
            has_table_privilege('myuser', schemaname||'.'||matviewname, 'INSERT') as myuser_insert
        FROM pg_matviews
        WHERE schemaname = 'mart' 
          AND matviewname IN ('mv_receive_daily', 'mv_target_card_per_day')
        ORDER BY matviewname;
    """
    result = op.get_bind().execute(sa.text(verify_sql))
    print("\n[PERMISSIONS] Materialized View Permissions:")
    print("Schema | MV Name                  | myuser_SELECT | myuser_INSERT")
    print("-------|--------------------------|---------------|---------------")
    for row in result:
        print(f"{row[0]:6} | {row[1]:24} | {str(row[2]):13} | {str(row[3]):13}")
    
    print("\n✅ [PERMISSIONS] Comprehensive permissions granted successfully")
    print("   Users: myuser, sanbou_app_dev, sanbou_app_stg, sanbou_app_prod")
    print("   Schemas: stg, mart, ref, kpi, tmp")
    print("   Permissions: Full CRUD + Materialized View REFRESH")


def downgrade():
    """
    Revoke comprehensive permissions from all application users
    
    Note: This is a partial downgrade as we cannot fully revert to unknown previous state.
    We revoke the granted permissions but don't restore any previous specific grants.
    """
    print("[PERMISSIONS] Revoking comprehensive permissions from all app users...")
    
    app_users = [
        'myuser',
        'sanbou_app_dev',
        'sanbou_app_stg',
        'sanbou_app_prod',
    ]
    
    schemas = ['stg', 'mart', 'ref', 'kpi', 'tmp']
    
    for user in app_users:
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
    
    print("✅ [PERMISSIONS] Permissions revoked")
