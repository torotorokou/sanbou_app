"""Add forecast schema and predictions_daily table

Revision ID: 20251215_140100
Revises: 20251215_140000
Create Date: 2025-12-15 14:01:00.000000

Description:
  - Create forecast schema
  - Create forecast.predictions_daily table for storing forecast results
  - Add indexes for performance
  - Grant permissions to app users

Usage:
  make al-up-v2-env ENV=local_dev
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251215_140100'
down_revision = '20251215_140000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create forecast.predictions_daily table for storing forecast results.
    """
    # Create forecast schema
    op.execute("CREATE SCHEMA IF NOT EXISTS forecast")
    
    # Create predictions_daily table
    op.create_table(
        'predictions_daily',
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('y_hat', sa.Numeric(), nullable=False),
        sa.Column('y_lo', sa.Numeric(), nullable=True),
        sa.Column('y_hi', sa.Numeric(), nullable=True),
        sa.Column('model_version', sa.String(), nullable=True),
        sa.Column('generated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('date'),
        schema='forecast'
    )
    
    # Create index on generated_at for queries
    op.create_index(
        'ix_predictions_daily_generated_at',
        'predictions_daily',
        ['generated_at'],
        schema='forecast'
    )
    
    # Grant permissions
    op.execute("""
        -- Grant usage on forecast schema to myuser
        GRANT USAGE ON SCHEMA forecast TO myuser;
        
        -- Grant all privileges on predictions_daily table to myuser
        GRANT SELECT, INSERT, UPDATE, DELETE ON forecast.predictions_daily TO myuser;
        
        -- Grant to app users if they exist
        DO $$
        BEGIN
            -- sanbou_app_dev
            IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'sanbou_app_dev') THEN
                GRANT USAGE ON SCHEMA forecast TO sanbou_app_dev;
                GRANT SELECT, INSERT, UPDATE, DELETE ON forecast.predictions_daily TO sanbou_app_dev;
            END IF;
            
            -- sanbou_app_stg
            IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'sanbou_app_stg') THEN
                GRANT USAGE ON SCHEMA forecast TO sanbou_app_stg;
                GRANT SELECT, INSERT, UPDATE, DELETE ON forecast.predictions_daily TO sanbou_app_stg;
            END IF;
            
            -- sanbou_app_prod
            IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'sanbou_app_prod') THEN
                GRANT USAGE ON SCHEMA forecast TO sanbou_app_prod;
                GRANT SELECT, INSERT, UPDATE, DELETE ON forecast.predictions_daily TO sanbou_app_prod;
            END IF;
            
            -- app_readonly
            IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_readonly') THEN
                GRANT USAGE ON SCHEMA forecast TO app_readonly;
                GRANT SELECT ON forecast.predictions_daily TO app_readonly;
            END IF;
        END
        $$;
    """)


def downgrade() -> None:
    """
    Drop forecast.predictions_daily table and forecast schema.
    """
    # Drop index
    op.drop_index('ix_predictions_daily_generated_at', table_name='predictions_daily', schema='forecast')
    
    # Drop table
    op.drop_table('predictions_daily', schema='forecast')
    
    # Drop schema (only if empty)
    op.execute("DROP SCHEMA IF EXISTS forecast CASCADE")
