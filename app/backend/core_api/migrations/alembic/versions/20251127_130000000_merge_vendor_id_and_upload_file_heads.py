"""merge vendor_id and upload_file heads

Revision ID: 20251127_130000000
Revises: 20251114_120000000, 20251127_120000000
Create Date: 2025-11-27 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251127_130000000'
down_revision = ('20251114_120000000', '20251127_120000000')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
