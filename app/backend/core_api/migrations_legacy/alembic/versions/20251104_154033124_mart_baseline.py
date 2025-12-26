"""mart_baseline

Revision ID: 20251104_154033124
Revises:
Create Date: 2025-11-04 06:40:33.866612
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as psql

# revision identifiers, used by Alembic.
revision = "20251104_154033124"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- mart.daily_target_plan ---
    # 現状：
    #   ddate       : timestamp without time zone (NULL)
    #   target_ton  : double precision (NULL)
    #   scope_used  : text (NULL)
    #   created_at  : timestamp without time zone (NULL)
    op.create_table(
        "daily_target_plan",
        sa.Column("ddate", sa.TIMESTAMP(timezone=False), nullable=True),
        sa.Column("target_ton", psql.DOUBLE_PRECISION(), nullable=True),
        sa.Column("scope_used", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=False), nullable=True),
        schema="mart",
    )

    # --- mart.inb_profile_smooth_test ---
    # 現状：
    #   scope           : text NOT NULL
    #   iso_week        : integer NOT NULL
    #   iso_dow         : integer NOT NULL
    #   day_mean_smooth : numeric NOT NULL
    #   method          : text NOT NULL
    #   params          : jsonb NOT NULL
    #   updated_at      : timestamptz NOT NULL DEFAULT now()
    #   PK              : (scope, iso_week, iso_dow)  名称: inb_profile_smooth_test_pkey
    op.create_table(
        "inb_profile_smooth_test",
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column("iso_week", sa.Integer(), nullable=False),
        sa.Column("iso_dow", sa.Integer(), nullable=False),
        sa.Column("day_mean_smooth", sa.Numeric(), nullable=False),
        sa.Column("method", sa.Text(), nullable=False),
        sa.Column("params", psql.JSONB(), nullable=False),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "scope",
            "iso_week",
            "iso_dow",
            name="inb_profile_smooth_test_pkey",
        ),
        schema="mart",
    )


def downgrade() -> None:
    op.drop_table("inb_profile_smooth_test", schema="mart")
    op.drop_table("daily_target_plan", schema="mart")
