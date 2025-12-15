"""Add jobs schema and forecast_jobs table

Revision ID: 20251215_140000
Revises: 20251212_100000000
Create Date: 2025-12-15 14:00:00.000000

Description:
  - Create jobs schema
  - Create jobs.forecast_jobs table for forecast job queue management
  - Add indexes for performance
  - Grant permissions to app users

Usage:
  make al-up-v2-env ENV=local_dev
  make al-up-v2-env ENV=vm_stg
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '20251215_140000'
down_revision = '20251212_100000000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create jobs.forecast_jobs table for forecast job queue management.
    """
    # Create jobs schema
    op.execute("CREATE SCHEMA IF NOT EXISTS jobs")
    
    # Create forecast_jobs table
    op.create_table(
        'forecast_jobs',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('job_type', sa.String(), nullable=False),
        sa.Column('target_from', sa.Date(), nullable=False),
        sa.Column('target_to', sa.Date(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('scheduled_for', sa.TIMESTAMP(), nullable=True),
        sa.Column('actor', sa.String(), nullable=True),
        sa.Column('payload_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        schema='jobs'
    )
    
    # Create indexes for performance
    op.create_index(
        'ix_forecast_jobs_status',
        'forecast_jobs',
        ['status'],
        schema='jobs'
    )
    op.create_index(
        'ix_forecast_jobs_created_at',
        'forecast_jobs',
        ['created_at'],
        schema='jobs'
    )
    op.create_index(
        'ix_forecast_jobs_target_dates',
        'forecast_jobs',
        ['target_from', 'target_to'],
        schema='jobs'
    )
    
    # Grant permissions to app users
    # Note: Grant to myuser (always exists) and optional app users if they exist
    
    op.execute("""
        -- Grant usage on jobs schema to myuser
        GRANT USAGE ON SCHEMA jobs TO myuser;
        
        -- Grant all privileges on forecast_jobs table to myuser
        GRANT SELECT, INSERT, UPDATE, DELETE ON jobs.forecast_jobs TO myuser;
        
        -- Grant sequence usage for autoincrement to myuser
        GRANT USAGE, SELECT ON SEQUENCE jobs.forecast_jobs_id_seq TO myuser;
        
        -- Grant to app users if they exist (ignore errors if they don't)
        DO $$
        BEGIN
            -- sanbou_app_dev
            IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'sanbou_app_dev') THEN
                GRANT USAGE ON SCHEMA jobs TO sanbou_app_dev;
                GRANT SELECT, INSERT, UPDATE, DELETE ON jobs.forecast_jobs TO sanbou_app_dev;
                GRANT USAGE, SELECT ON SEQUENCE jobs.forecast_jobs_id_seq TO sanbou_app_dev;
            END IF;
            
            -- sanbou_app_stg
            IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'sanbou_app_stg') THEN
                GRANT USAGE ON SCHEMA jobs TO sanbou_app_stg;
                GRANT SELECT, INSERT, UPDATE, DELETE ON jobs.forecast_jobs TO sanbou_app_stg;
                GRANT USAGE, SELECT ON SEQUENCE jobs.forecast_jobs_id_seq TO sanbou_app_stg;
            END IF;
            
            -- sanbou_app_prod
            IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'sanbou_app_prod') THEN
                GRANT USAGE ON SCHEMA jobs TO sanbou_app_prod;
                GRANT SELECT, INSERT, UPDATE, DELETE ON jobs.forecast_jobs TO sanbou_app_prod;
                GRANT USAGE, SELECT ON SEQUENCE jobs.forecast_jobs_id_seq TO sanbou_app_prod;
            END IF;
            
            -- app_readonly
            IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_readonly') THEN
                GRANT USAGE ON SCHEMA jobs TO app_readonly;
                GRANT SELECT ON jobs.forecast_jobs TO app_readonly;
            END IF;
        END
        $$;
    """)
    
    # Create updated_at trigger for automatic timestamp update
    op.execute("""
        CREATE OR REPLACE FUNCTION jobs.update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        CREATE TRIGGER update_forecast_jobs_updated_at
        BEFORE UPDATE ON jobs.forecast_jobs
        FOR EACH ROW
        EXECUTE FUNCTION jobs.update_updated_at_column();
    """)


def downgrade() -> None:
    """
    Drop jobs.forecast_jobs table and jobs schema.
    """
    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS update_forecast_jobs_updated_at ON jobs.forecast_jobs")
    op.execute("DROP FUNCTION IF EXISTS jobs.update_updated_at_column()")
    
    # Drop indexes
    op.drop_index('ix_forecast_jobs_target_dates', table_name='forecast_jobs', schema='jobs')
    op.drop_index('ix_forecast_jobs_created_at', table_name='forecast_jobs', schema='jobs')
    op.drop_index('ix_forecast_jobs_status', table_name='forecast_jobs', schema='jobs')
    
    # Drop table
    op.drop_table('forecast_jobs', schema='jobs')
    
    # Drop schema (only if empty)
    op.execute("DROP SCHEMA IF EXISTS jobs CASCADE")
