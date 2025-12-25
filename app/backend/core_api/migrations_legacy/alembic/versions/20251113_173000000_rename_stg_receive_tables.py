"""Rename stg tables to *_shogun_flash format

Revision ID: 20251113_173000000
Revises: 20251113_172000000
Create Date: 2025-11-13 17:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20251113_173000000"
down_revision: Union[str, None] = "20251113_172000000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    stg層のテーブル名を *_shogun_flash 形式に統一
    - stg.receive → stg.receive_shogun_flash (既に存在する場合はスキップ)
    - stg.yard → stg.yard_shogun_flash
    - stg.shipment → stg.shipment_shogun_flash
    """
    # stg.receive が存在する場合は receive_shogun_flash に戻す
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables
                      WHERE table_schema = 'stg' AND table_name = 'receive') THEN
                ALTER TABLE stg.receive RENAME TO receive_shogun_flash;
            END IF;
        END $$;
    """
    )

    # stg.yard → stg.yard_shogun_flash
    op.execute("ALTER TABLE stg.yard RENAME TO yard_shogun_flash;")

    # stg.shipment → stg.shipment_shogun_flash
    op.execute("ALTER TABLE stg.shipment RENAME TO shipment_shogun_flash;")


def downgrade() -> None:
    """
    ロールバック: *_shogun_flash を元の名前に戻す
    """
    op.execute("ALTER TABLE stg.receive_shogun_flash RENAME TO receive;")
    op.execute("ALTER TABLE stg.yard_shogun_flash RENAME TO yard;")
    op.execute("ALTER TABLE stg.shipment_shogun_flash RENAME TO shipment;")
