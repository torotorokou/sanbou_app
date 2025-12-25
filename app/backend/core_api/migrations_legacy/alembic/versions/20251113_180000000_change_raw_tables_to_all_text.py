"""Change raw.*_shogun_flash and *_shogun_final tables to all TEXT columns

Revision ID: 20251113_180000000
Revises: 20251113_175000000
Create Date: 2025-11-13 18:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20251113_180000000"
down_revision: Union[str, None] = "20251113_175000000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    raw層のテーブルを削除して、全カラムTEXT型で再作成
    生データを保存するため、型変換なしでそのまま保存する
    """

    # 既存のraw層テーブルを削除
    op.execute("DROP TABLE IF EXISTS raw.receive_shogun_flash CASCADE;")
    op.execute("DROP TABLE IF EXISTS raw.receive_shogun_final CASCADE;")
    op.execute("DROP TABLE IF EXISTS raw.yard_shogun_flash CASCADE;")
    op.execute("DROP TABLE IF EXISTS raw.yard_shogun_final CASCADE;")
    op.execute("DROP TABLE IF EXISTS raw.shipment_shogun_flash CASCADE;")
    op.execute("DROP TABLE IF EXISTS raw.shipment_shogun_final CASCADE;")

    # raw.receive_shogun_flash を全カラムTEXT型で作成
    op.execute(
        """
        CREATE TABLE raw.receive_shogun_flash (
            slip_date TEXT,
            sales_date TEXT,
            payment_date TEXT,
            vendor_cd TEXT,
            vendor_name TEXT,
            slip_type_cd TEXT,
            slip_type_name TEXT,
            item_cd TEXT,
            item_name TEXT,
            net_weight TEXT,
            quantity TEXT,
            unit_cd TEXT,
            unit_name TEXT,
            unit_price TEXT,
            amount TEXT,
            receive_no TEXT,
            aggregate_item_cd TEXT,
            aggregate_item_name TEXT,
            category_cd TEXT,
            category_name TEXT,
            weighing_time_gross TEXT,
            weighing_time_empty TEXT,
            site_cd TEXT,
            site_name TEXT,
            unload_vendor_cd TEXT,
            unload_vendor_name TEXT,
            unload_site_cd TEXT,
            unload_site_name TEXT,
            transport_vendor_cd TEXT,
            transport_vendor_name TEXT,
            client_cd TEXT,
            client_name TEXT,
            manifest_type_cd TEXT,
            manifest_type_name TEXT,
            sales_staff_cd TEXT,
            sales_staff_name TEXT,
            manifest_no TEXT,
            column38 TEXT,
            column39 TEXT
        );
    """
    )

    # raw.receive_shogun_final も同じ構造で作成
    op.execute(
        """
        CREATE TABLE raw.receive_shogun_final (
            slip_date TEXT,
            sales_date TEXT,
            payment_date TEXT,
            vendor_cd TEXT,
            vendor_name TEXT,
            slip_type_cd TEXT,
            slip_type_name TEXT,
            item_cd TEXT,
            item_name TEXT,
            net_weight TEXT,
            quantity TEXT,
            unit_cd TEXT,
            unit_name TEXT,
            unit_price TEXT,
            amount TEXT,
            receive_no TEXT,
            aggregate_item_cd TEXT,
            aggregate_item_name TEXT,
            category_cd TEXT,
            category_name TEXT,
            weighing_time_gross TEXT,
            weighing_time_empty TEXT,
            site_cd TEXT,
            site_name TEXT,
            unload_vendor_cd TEXT,
            unload_vendor_name TEXT,
            unload_site_cd TEXT,
            unload_site_name TEXT,
            transport_vendor_cd TEXT,
            transport_vendor_name TEXT,
            client_cd TEXT,
            client_name TEXT,
            manifest_type_cd TEXT,
            manifest_type_name TEXT,
            sales_staff_cd TEXT,
            sales_staff_name TEXT,
            manifest_no TEXT,
            column38 TEXT,
            column39 TEXT
        );
    """
    )

    # raw.yard_shogun_flash を全カラムTEXT型で作成
    op.execute(
        """
        CREATE TABLE raw.yard_shogun_flash (
            slip_date TEXT,
            client_en_name TEXT,
            item_en_name TEXT,
            net_weight TEXT,
            quantity TEXT,
            unit_en_name TEXT,
            unit_price TEXT,
            amount TEXT,
            sales_staff_en_name TEXT,
            vendor_cd TEXT,
            vendor_en_name TEXT,
            category_cd TEXT,
            category_en_name TEXT,
            item_cd TEXT,
            slip_no TEXT
        );
    """
    )

    # raw.yard_shogun_final も同じ構造で作成
    op.execute(
        """
        CREATE TABLE raw.yard_shogun_final (
            slip_date TEXT,
            client_en_name TEXT,
            item_en_name TEXT,
            net_weight TEXT,
            quantity TEXT,
            unit_en_name TEXT,
            unit_price TEXT,
            amount TEXT,
            sales_staff_en_name TEXT,
            vendor_cd TEXT,
            vendor_en_name TEXT,
            category_cd TEXT,
            category_en_name TEXT,
            item_cd TEXT,
            slip_no TEXT
        );
    """
    )

    # raw.shipment_shogun_flash を全カラムTEXT型で作成
    op.execute(
        """
        CREATE TABLE raw.shipment_shogun_flash (
            slip_date TEXT,
            client_en_name TEXT,
            item_en_name TEXT,
            net_weight TEXT,
            quantity TEXT,
            unit_en_name TEXT,
            unit_price TEXT,
            amount TEXT,
            transport_vendor_en_name TEXT,
            vendor_cd TEXT,
            vendor_en_name TEXT,
            site_cd TEXT,
            site_en_name TEXT,
            slip_type_en_name TEXT,
            shipment_no TEXT,
            detail_note TEXT,
            id TEXT,
            created_at TEXT
        );
    """
    )

    # raw.shipment_shogun_final も同じ構造で作成
    op.execute(
        """
        CREATE TABLE raw.shipment_shogun_final (
            slip_date TEXT,
            client_en_name TEXT,
            item_en_name TEXT,
            net_weight TEXT,
            quantity TEXT,
            unit_en_name TEXT,
            unit_price TEXT,
            amount TEXT,
            transport_vendor_en_name TEXT,
            vendor_cd TEXT,
            vendor_en_name TEXT,
            site_cd TEXT,
            site_en_name TEXT,
            slip_type_en_name TEXT,
            shipment_no TEXT,
            detail_note TEXT,
            id TEXT,
            created_at TEXT
        );
    """
    )


def downgrade() -> None:
    """
    ロールバック: raw層のテーブルを型付きで再作成（前の状態に戻す）
    """
    # TEXT型テーブルを削除
    op.execute("DROP TABLE IF EXISTS raw.receive_shogun_flash CASCADE;")
    op.execute("DROP TABLE IF EXISTS raw.receive_shogun_final CASCADE;")
    op.execute("DROP TABLE IF EXISTS raw.yard_shogun_flash CASCADE;")
    op.execute("DROP TABLE IF EXISTS raw.yard_shogun_final CASCADE;")
    op.execute("DROP TABLE IF EXISTS raw.shipment_shogun_flash CASCADE;")
    op.execute("DROP TABLE IF EXISTS raw.shipment_shogun_final CASCADE;")

    # 型付きテーブルで再作成
    op.execute(
        "CREATE TABLE raw.receive_shogun_flash (LIKE stg.receive_shogun_flash INCLUDING ALL);"
    )
    op.execute(
        "CREATE TABLE raw.receive_shogun_final (LIKE stg.receive_shogun_final INCLUDING ALL);"
    )
    op.execute(
        "CREATE TABLE raw.yard_shogun_flash (LIKE stg.yard_shogun_flash INCLUDING ALL);"
    )
    op.execute(
        "CREATE TABLE raw.yard_shogun_final (LIKE stg.yard_shogun_final INCLUDING ALL);"
    )
    op.execute(
        "CREATE TABLE raw.shipment_shogun_flash (LIKE stg.shipment_shogun_flash INCLUDING ALL);"
    )
    op.execute(
        "CREATE TABLE raw.shipment_shogun_final (LIKE stg.shipment_shogun_final INCLUDING ALL);"
    )
