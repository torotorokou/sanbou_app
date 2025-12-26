"""rename columns remove en suffix

Revision ID: 20251114_092500000
Revises: 20251113_180000000
Create Date: 2025-11-14

Description:
    YAMLで定義されたカラム名から冗長な _en_ 接尾辞を削除するため、
    raw/stgスキーマのshipment/yardテーブルのカラム名をリネーム。

    対象:
    - raw.shipment_shogun_flash/final
    - raw.yard_shogun_flash/final
    - stg.shipment_shogun_flash/final
    - stg.yard_shogun_flash/final

    変更:
    - client_en_name → client_name
    - vendor_en_name → vendor_name
    - site_en_name → site_name
    - item_en_name → item_name
    - unit_en_name → unit_name
    - transport_vendor_en_name → transport_vendor_name
    - slip_type_en_name → slip_type_name
    - sales_staff_en_name → sales_staff_name (yard のみ)
    - category_en_name → category_name
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20251114_092500000"
down_revision: str | None = "20251113_180000000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    カラム名から _en_ 接尾辞を削除
    """

    # ========================================
    # shipment テーブル群 (7カラム)
    # ========================================
    shipment_renames = [
        ("client_en_name", "client_name"),
        ("vendor_en_name", "vendor_name"),
        ("site_en_name", "site_name"),
        ("item_en_name", "item_name"),
        ("unit_en_name", "unit_name"),
        ("transport_vendor_en_name", "transport_vendor_name"),
        ("slip_type_en_name", "slip_type_name"),
    ]

    for schema in ["raw", "stg"]:
        for table in ["shipment_shogun_flash", "shipment_shogun_final"]:
            for old_name, new_name in shipment_renames:
                op.execute(
                    f"ALTER TABLE {schema}.{table} " f"RENAME COLUMN {old_name} TO {new_name}"
                )

    # ========================================
    # yard テーブル群 (6カラム + sales_staff)
    # ========================================
    yard_renames = [
        ("client_en_name", "client_name"),
        ("item_en_name", "item_name"),
        ("unit_en_name", "unit_name"),
        ("sales_staff_en_name", "sales_staff_name"),
        ("vendor_en_name", "vendor_name"),
        ("category_en_name", "category_name"),
    ]

    for schema in ["raw", "stg"]:
        for table in ["yard_shogun_flash", "yard_shogun_final"]:
            for old_name, new_name in yard_renames:
                op.execute(
                    f"ALTER TABLE {schema}.{table} " f"RENAME COLUMN {old_name} TO {new_name}"
                )

    print("✅ All _en_ suffix columns renamed successfully")


def downgrade() -> None:
    """
    カラム名を元に戻す (ロールバック用)
    """

    # ========================================
    # shipment テーブル群 (逆順)
    # ========================================
    shipment_renames_reverse = [
        ("client_name", "client_en_name"),
        ("vendor_name", "vendor_en_name"),
        ("site_name", "site_en_name"),
        ("item_name", "item_en_name"),
        ("unit_name", "unit_en_name"),
        ("transport_vendor_name", "transport_vendor_en_name"),
        ("slip_type_name", "slip_type_en_name"),
    ]

    for schema in ["raw", "stg"]:
        for table in ["shipment_shogun_flash", "shipment_shogun_final"]:
            for old_name, new_name in shipment_renames_reverse:
                op.execute(
                    f"ALTER TABLE {schema}.{table} " f"RENAME COLUMN {old_name} TO {new_name}"
                )

    # ========================================
    # yard テーブル群 (逆順)
    # ========================================
    yard_renames_reverse = [
        ("client_name", "client_en_name"),
        ("item_name", "item_en_name"),
        ("unit_name", "unit_en_name"),
        ("sales_staff_name", "sales_staff_en_name"),
        ("vendor_name", "vendor_en_name"),
        ("category_name", "category_en_name"),
    ]

    for schema in ["raw", "stg"]:
        for table in ["yard_shogun_flash", "yard_shogun_final"]:
            for old_name, new_name in yard_renames_reverse:
                op.execute(
                    f"ALTER TABLE {schema}.{table} " f"RENAME COLUMN {old_name} TO {new_name}"
                )

    print("⏪ All columns reverted to _en_ suffix naming")
