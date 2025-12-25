"""manage views: mart.*

Revision ID: 20251104_160703155
Revises: 20251104_154033124
Create Date: 2025-11-04 07:07:03.956955

"""

from pathlib import Path

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20251104_160703155"
down_revision = "20251104_154033124"
branch_labels = None
depends_on = None


BASE = Path("/backend/migrations/alembic/sql/mart")


def _sql(name: str) -> str:
    return (BASE / name).read_text(encoding="utf-8")


def upgrade():
    op.execute(_sql("receive_daily.sql"))
    op.execute(_sql("receive_weekly.sql"))
    op.execute(_sql("receive_monthly.sql"))
    op.execute(_sql("v_daily_target_with_calendar.sql"))
    op.execute(_sql("v_target_card_per_day.sql"))


def downgrade():
    pass  # ここは空でOK（必要なら後で整備）
