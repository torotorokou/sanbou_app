"""Create raw.*_shogun_flash and *_shogun_final tables

Revision ID: 20251113_175000000
Revises: 20251113_174000000
Create Date: 2025-11-13 17:50:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20251113_175000000"
down_revision: str | None = "20251113_174000000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    raw層に *_shogun_flash / *_shogun_final テーブルを作成
    stg層と同じ構造（型付き）でデータを保存

    テーブル名:
    - raw.receive_shogun_flash / raw.receive_shogun_final
    - raw.yard_shogun_flash / raw.yard_shogun_final
    - raw.shipment_shogun_flash / raw.shipment_shogun_final
    """

    # raw.receive_shogun_flash を作成（stg.receive_shogun_flash と同じ構造）
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS raw.receive_shogun_flash (LIKE stg.receive_shogun_flash INCLUDING ALL);
    """
    )

    # raw.receive_shogun_final を作成
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS raw.receive_shogun_final (LIKE stg.receive_shogun_final INCLUDING ALL);
    """
    )

    # raw.yard_shogun_flash を作成
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS raw.yard_shogun_flash (LIKE stg.yard_shogun_flash INCLUDING ALL);
    """
    )

    # raw.yard_shogun_final を作成
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS raw.yard_shogun_final (LIKE stg.yard_shogun_final INCLUDING ALL);
    """
    )

    # raw.shipment_shogun_flash を作成
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS raw.shipment_shogun_flash (LIKE stg.shipment_shogun_flash INCLUDING ALL);
    """
    )

    # raw.shipment_shogun_final を作成
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS raw.shipment_shogun_final (LIKE stg.shipment_shogun_final INCLUDING ALL);
    """
    )


def downgrade() -> None:
    """
    ロールバック: raw層の *_shogun_flash / *_shogun_final テーブルを削除
    """
    op.execute("DROP TABLE IF EXISTS raw.receive_shogun_flash;")
    op.execute("DROP TABLE IF EXISTS raw.receive_shogun_final;")
    op.execute("DROP TABLE IF EXISTS raw.yard_shogun_flash;")
    op.execute("DROP TABLE IF EXISTS raw.yard_shogun_final;")
    op.execute("DROP TABLE IF EXISTS raw.shipment_shogun_flash;")
    op.execute("DROP TABLE IF EXISTS raw.shipment_shogun_final;")
