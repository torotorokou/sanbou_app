"""drop stg.v_king_receive_clean_legacy

Revision ID: 20251105_174743743
Revises: 20251105_174522163
Create Date: 2025-11-05 08:47:44.515740

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251105_174743743'
down_revision = '20251105_174522163'
branch_labels = None
depends_on = None


def upgrade():
    with op.get_context().autocommit_block():
        op.execute(sa.text("DROP VIEW IF EXISTS stg.v_king_receive_clean_legacy;"))

def downgrade():
    # 復元不要なら no-op でOK。必要なら旧定義をここに再掲。
    with op.get_context().autocommit_block():
        op.execute(sa.text("DO $$ BEGIN RAISE NOTICE 'no-op downgrade for %', :rev; END $$;"),
                   {"rev": revision})