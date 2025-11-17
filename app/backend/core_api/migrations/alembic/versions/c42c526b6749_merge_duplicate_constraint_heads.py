"""merge duplicate constraint heads

Revision ID: c42c526b6749
Revises: 20251114_130200000, 20251114_200000000
Create Date: 2025-11-14 09:03:04.320994

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c42c526b6749'
down_revision = ('20251114_130200000', '20251114_200000000')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
