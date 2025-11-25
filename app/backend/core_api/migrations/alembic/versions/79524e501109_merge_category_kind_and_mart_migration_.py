"""merge category_kind and mart migration heads

Revision ID: 79524e501109
Revises: 20251125_110000000, 20251125_112732912
Create Date: 2025-11-25 04:41:09.308893

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '79524e501109'
down_revision = ('20251125_110000000', '20251125_112732912')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
