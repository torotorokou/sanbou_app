"""merge_mv_unique_index_heads

Revision ID: 20251212_110000000
Revises: 20251212_100000000, 5954d9f2b9bf
Create Date: 2025-12-12 10:20:44.180214

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251212_110000000'
down_revision = ('20251212_100000000', '5954d9f2b9bf')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
