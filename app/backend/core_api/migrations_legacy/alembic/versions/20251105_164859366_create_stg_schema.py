"""create stg schema

Revision ID: 20251105_164859366
Revises: 20251105_160859083
Create Date: 2025-11-05 07:49:00.148622

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251105_164859366"
down_revision = "20251105_160859083"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE SCHEMA IF NOT EXISTS stg;")
    # 必要に応じて権限（例：myuserロールに使用許可）
    op.execute("GRANT USAGE ON SCHEMA stg TO myuser;")


def downgrade():
    # 先に配下オブジェクトを消す必要があるため通常はDROPしない運用を推奨
    pass
