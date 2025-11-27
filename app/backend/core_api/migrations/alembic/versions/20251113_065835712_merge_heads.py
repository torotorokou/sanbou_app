"""merge heads

Revision ID: 20251113_065835712
Revises: 20251113_151556000, 20251113_170000000
Create Date: 2025-11-13 06:58:35.712213

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251113_065835712'
down_revision = ('20251113_151556000', '20251113_170000000')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
