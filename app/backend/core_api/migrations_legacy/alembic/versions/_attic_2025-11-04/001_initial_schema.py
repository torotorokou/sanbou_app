"""Initial schema: jobs, forecast, core - ARCHIVED

【アーカイブ理由】
DBにベースライン未刻印のため未適用。
新運用では単一ベースライン(9a092c4a1fcf)から再構築するため、このリビジョンは使用しません。
参照・検証目的でのみ保全しています。

Revision ID: 001
Revises:
Create Date: 2025-10-06 00:00:00

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create schemas
    op.execute("CREATE SCHEMA IF NOT EXISTS jobs")
    op.execute("CREATE SCHEMA IF NOT EXISTS forecast")
    op.execute("CREATE SCHEMA IF NOT EXISTS core")

    # jobs.forecast_jobs
    op.create_table(
        "forecast_jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("job_type", sa.String(), nullable=False),
        sa.Column("target_from", sa.Date(), nullable=False),
        sa.Column("target_to", sa.Date(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("scheduled_for", sa.TIMESTAMP(), nullable=True),
        sa.Column("actor", sa.String(), nullable=True),
        sa.Column(
            "payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="jobs",
    )
    op.create_index(
        "ix_jobs_forecast_jobs_status",
        "forecast_jobs",
        ["status"],
        unique=False,
        schema="jobs",
    )

    # forecast.predictions_daily
    op.create_table(
        "predictions_daily",
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("y_hat", sa.Numeric(), nullable=False),
        sa.Column("y_lo", sa.Numeric(), nullable=True),
        sa.Column("y_hi", sa.Numeric(), nullable=True),
        sa.Column("model_version", sa.String(), nullable=True),
        sa.Column(
            "generated_at",
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.PrimaryKeyConstraint("date"),
        schema="forecast",
    )

    # core.inbound_actuals
    op.create_table(
        "inbound_actuals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("data_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="core",
    )
    op.create_index(
        "ix_core_inbound_actuals_date",
        "inbound_actuals",
        ["date"],
        unique=False,
        schema="core",
    )

    # core.inbound_reservations
    op.create_table(
        "inbound_reservations",
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("trucks", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.PrimaryKeyConstraint("date"),
        schema="core",
    )


def downgrade() -> None:
    op.drop_table("inbound_reservations", schema="core")
    op.drop_table("inbound_actuals", schema="core")
    op.drop_table("predictions_daily", schema="forecast")
    op.drop_table("forecast_jobs", schema="jobs")
    op.execute("DROP SCHEMA IF EXISTS core CASCADE")
    op.execute("DROP SCHEMA IF EXISTS forecast CASCADE")
    op.execute("DROP SCHEMA IF EXISTS jobs CASCADE")
