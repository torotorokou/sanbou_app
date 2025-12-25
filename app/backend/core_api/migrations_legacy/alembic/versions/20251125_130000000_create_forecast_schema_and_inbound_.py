"""create forecast schema and inbound forecast tables

Revision ID: 20251125_130000000
Revises: 20251125_120000000
Create Date: 2025-11-25 09:09:17.042004

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251125_130000000"
down_revision = "20251125_120000000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create forecast schema and inbound forecast tables

    Purpose: ML-based inbound forecasting system
    Tables:
    - inbound_forecast_run: forecast run metadata
    - inbound_forecast_monthly_raw: monthly forecast results
    - inbound_forecast_weekly_raw: weekly forecast results
    - inbound_forecast_daily: daily forecast results (allocated from monthly/weekly)
    """

    print("[forecast] Creating schema...")
    op.execute("CREATE SCHEMA IF NOT EXISTS forecast")

    print("[forecast] Creating inbound_forecast_run table...")
    op.execute(
        """
        CREATE TABLE forecast.inbound_forecast_run (
            run_id BIGSERIAL PRIMARY KEY,
            factory_id TEXT NOT NULL,
            target_month DATE NOT NULL,
            model_name TEXT NOT NULL,
            run_type TEXT NOT NULL,
            run_datetime TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            horizon_start DATE,
            horizon_end DATE,
            allocation_method TEXT,
            train_from DATE,
            train_to DATE,
            notes TEXT
        )
    """
    )

    print("[forecast] Creating inbound_forecast_monthly_raw table...")
    op.execute(
        """
        CREATE TABLE forecast.inbound_forecast_monthly_raw (
            run_id BIGINT NOT NULL,
            target_month DATE NOT NULL,
            p50_ton NUMERIC(18,3) NOT NULL,
            p10_ton NUMERIC(18,3),
            p90_ton NUMERIC(18,3),
            scenario TEXT NOT NULL DEFAULT 'base',
            PRIMARY KEY (run_id, target_month, scenario),
            FOREIGN KEY (run_id) REFERENCES forecast.inbound_forecast_run(run_id)
        )
    """
    )

    print("[forecast] Creating inbound_forecast_weekly_raw table...")
    op.execute(
        """
        CREATE TABLE forecast.inbound_forecast_weekly_raw (
            run_id BIGINT NOT NULL,
            target_week_start DATE NOT NULL,
            p50_ton NUMERIC(18,3) NOT NULL,
            p10_ton NUMERIC(18,3),
            p90_ton NUMERIC(18,3),
            scenario TEXT NOT NULL DEFAULT 'base',
            PRIMARY KEY (run_id, target_week_start, scenario),
            FOREIGN KEY (run_id) REFERENCES forecast.inbound_forecast_run(run_id)
        )
    """
    )

    print("[forecast] Creating inbound_forecast_daily table...")
    op.execute(
        """
        CREATE TABLE forecast.inbound_forecast_daily (
            run_id BIGINT NOT NULL,
            target_date DATE NOT NULL,
            horizon_days INTEGER,
            p50_ton NUMERIC(18,3) NOT NULL,
            p10_ton NUMERIC(18,3),
            p90_ton NUMERIC(18,3),
            scenario TEXT NOT NULL DEFAULT 'base',
            PRIMARY KEY (run_id, target_date, scenario),
            FOREIGN KEY (run_id) REFERENCES forecast.inbound_forecast_run(run_id)
        )
    """
    )

    print("[ok] forecast schema and tables created")


def downgrade() -> None:
    """Drop forecast schema and all tables"""
    print("[forecast] Dropping schema and tables...")
    op.execute("DROP SCHEMA IF EXISTS forecast CASCADE")
