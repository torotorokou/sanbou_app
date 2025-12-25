"""merge heads: 20251210_130000000 and 20251211_100000000

Revision ID: 20251211_110000000
Revises: 20251210_130000000, 20251211_100000000
Create Date: 2025-12-11 11:00:00
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20251211_110000000"
down_revision = ("20251210_130000000", "20251211_100000000")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Merge migration - no changes"""
    pass


def downgrade() -> None:
    """Merge migration - no changes"""
    pass
