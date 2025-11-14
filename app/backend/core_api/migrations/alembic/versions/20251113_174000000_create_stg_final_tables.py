"""Create stg *_shogun_final tables

Revision ID: 20251113_174000000
Revises: 20251113_173000000
Create Date: 2025-11-13 17:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251113_174000000'
down_revision: Union[str, None] = '20251113_173000000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    stg層に *_shogun_final テーブルを作成（*_shogun_flash と同じ構造）
    - stg.yard_shogun_final
    - stg.shipment_shogun_final
    - stg.receive_shogun_final は既に存在するためスキップ
    """
    
    # stg.yard_shogun_final を作成（stg.yard_shogun_flash と同じ構造）
    op.execute("""
        CREATE TABLE IF NOT EXISTS stg.yard_shogun_final (LIKE stg.yard_shogun_flash INCLUDING ALL);
    """)
    
    # stg.shipment_shogun_final を作成（stg.shipment_shogun_flash と同じ構造）
    op.execute("""
        CREATE TABLE IF NOT EXISTS stg.shipment_shogun_final (LIKE stg.shipment_shogun_flash INCLUDING ALL);
    """)


def downgrade() -> None:
    """
    ロールバック: *_shogun_final テーブルを削除
    """
    op.execute('DROP TABLE IF EXISTS stg.yard_shogun_final;')
    op.execute('DROP TABLE IF EXISTS stg.shipment_shogun_final;')
