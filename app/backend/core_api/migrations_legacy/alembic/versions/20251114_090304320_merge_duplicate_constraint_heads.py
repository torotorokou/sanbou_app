"""merge duplicate constraint heads

Revision ID: 20251114_090304320
Revises: 20251114_130200000, 20251114_200000000
Create Date: 2025-11-14 09:03:04.320994

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20251114_090304320"
down_revision = ("20251114_130200000", "20251114_200000000")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
