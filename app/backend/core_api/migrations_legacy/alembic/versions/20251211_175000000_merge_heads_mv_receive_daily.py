"""merge_heads_mv_receive_daily

Revision ID: 20251211_175000000
Revises: 20251211_170000000, 20251211_145000000
Create Date: 2025-12-11 17:50:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20251211_175000000"
down_revision = ("20251211_170000000", "20251211_145000000")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
