"""baseline (no-op)

このリビジョンは Alembic 管理の起点（ベースライン）です。
既存のDBスキーマに対して何も変更を加えず、単に alembic_version テーブルに
このリビジョンIDを刻印することで、以降の差分マイグレーションを適用可能にします。

Revision ID: 9a092c4a1fcf
Revises: None
Create Date: 2025-11-04 00:49:59.978622

"""

# revision identifiers, used by Alembic.
revision = "9a092c4a1fcf"
down_revision = None  # ベースラインは親を持たない
branch_labels = None
depends_on = None


def upgrade() -> None:
    """既存DBに対して何も変更しない（No-Op）"""
    pass


def downgrade() -> None:
    """ダウングレードは想定しない（ベースライン）"""
    pass
