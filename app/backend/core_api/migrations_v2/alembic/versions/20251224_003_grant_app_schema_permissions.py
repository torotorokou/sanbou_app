"""grant_app_schema_permissions

Revision ID: 20251224_003
Revises: 20251224_002
Create Date: 2025-12-24

Purpose:
  Grant permissions on app schema to environment-specific database user.
  Required for announcements tables created in app schema.

Target User:
  - Determined by POSTGRES_USER environment variable
  - local_dev: myuser or sanbou_app_dev

Permissions Granted:
  - USAGE on app schema
  - SELECT, INSERT, UPDATE, DELETE on all tables
  - USAGE, SELECT on all sequences
"""
from alembic import op
import os


# revision identifiers, used by Alembic.
revision = '20251224_003'
down_revision = '20251224_002'
branch_labels = None
depends_on = None


def upgrade():
    """
    Grant permissions on app schema to current environment's user
    """
    # Get the current environment's database user from DB_USER or POSTGRES_USER env var
    # Prioritize DB_USER, fall back to POSTGRES_USER for backward compatibility
    current_user = os.environ.get('DB_USER') or os.environ.get('POSTGRES_USER')
    if not current_user:
        raise ValueError(
            "Database user not specified. Please set DB_USER or POSTGRES_USER environment variable.\n"
            "Example: DB_USER=sanbou_app_dev or POSTGRES_USER=sanbou_app_dev"
        )
    schema = 'app'
    
    print(f"[PERMISSIONS] Granting permissions on schema {schema} to user {current_user}")
    
    grant_sql = f"""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{current_user}') THEN
                IF EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = '{schema}') THEN
                    -- Grant USAGE on schema
                    EXECUTE 'GRANT USAGE ON SCHEMA {schema} TO {current_user}';
                    
                    -- Grant ALL privileges on all tables in schema
                    EXECUTE 'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {schema} TO {current_user}';
                    
                    -- Grant ALL privileges on all sequences in schema
                    EXECUTE 'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {schema} TO {current_user}';
                    
                    -- Grant default privileges for future tables
                    EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {current_user}';
                    
                    -- Grant default privileges for future sequences
                    EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT USAGE, SELECT ON SEQUENCES TO {current_user}';
                    
                    RAISE NOTICE 'Granted permissions on schema {schema} to {current_user}';
                ELSE
                    RAISE WARNING 'Schema {schema} does not exist!';
                END IF;
            ELSE
                RAISE WARNING 'User {current_user} does not exist!';
            END IF;
        END $$;
    """
    op.execute(grant_sql)


def downgrade():
    """
    Revoke permissions on app schema (typically not done in practice)
    """
    # Get the current environment's database user from DB_USER or POSTGRES_USER env var
    current_user = os.environ.get('DB_USER') or os.environ.get('POSTGRES_USER')
    if not current_user:
        raise ValueError(
            "Database user not specified. Please set DB_USER or POSTGRES_USER environment variable."
        )
    schema = 'app'
    
    revoke_sql = f"""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{current_user}') THEN
                IF EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = '{schema}') THEN
                    EXECUTE 'REVOKE SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {schema} FROM {current_user}';
                    EXECUTE 'REVOKE USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {schema} FROM {current_user}';
                    EXECUTE 'REVOKE USAGE ON SCHEMA {schema} FROM {current_user}';
                    RAISE NOTICE 'Revoked permissions on schema {schema} from {current_user}';
                END IF;
            END IF;
        END $$;
    """
    op.execute(revoke_sql)
