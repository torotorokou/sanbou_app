"""rename raw shogun tables to csv_kind format

Revision ID: 20251120_092912697
Revises: 20251120_091427843
Create Date: 2025-11-20 09:29:12

将軍CSVのrawテーブル名を csv_kind 命名規則に統一します（stgと同じ命名規則）。

変更内容:
  raw.receive_shogun_flash   → raw.shogun_flash_receive
  raw.shipment_shogun_flash  → raw.shogun_flash_shipment
  raw.yard_shogun_flash      → raw.shogun_flash_yard
  raw.receive_shogun_final   → raw.shogun_final_receive
  raw.shipment_shogun_final  → raw.shogun_final_shipment
  raw.yard_shogun_final      → raw.shogun_final_yard

命名規則: raw.{system}_{version}_{direction}
  - system: shogun
  - version: flash (速報版) / final (確定版)
  - direction: receive (受入) / shipment (出荷) / yard (ヤード)
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20251120_092912697"
down_revision = "20251120_091427843"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    rawテーブルをcsv_kind命名規則にリネーム
    """
    # 1. テーブルリネーム（6テーブル）
    renames = [
        ("receive_shogun_flash", "shogun_flash_receive"),
        ("shipment_shogun_flash", "shogun_flash_shipment"),
        ("yard_shogun_flash", "shogun_flash_yard"),
        ("receive_shogun_final", "shogun_final_receive"),
        ("shipment_shogun_final", "shogun_final_shipment"),
        ("yard_shogun_final", "shogun_final_yard"),
    ]

    for old_name, new_name in renames:
        op.execute(f"ALTER TABLE raw.{old_name} RENAME TO {new_name};")

    # 2. インデックス名もリネーム（存在する場合）
    index_renames = [
        # receive flash
        (
            "idx_receive_shogun_flash_upload_file_id",
            "idx_shogun_flash_receive_upload_file_id",
        ),
        # shipment flash
        (
            "idx_shipment_shogun_flash_upload_file_id",
            "idx_shogun_flash_shipment_upload_file_id",
        ),
        # yard flash
        (
            "idx_yard_shogun_flash_upload_file_id",
            "idx_shogun_flash_yard_upload_file_id",
        ),
        # receive final
        (
            "idx_receive_shogun_final_upload_file_id",
            "idx_shogun_final_receive_upload_file_id",
        ),
        # shipment final
        (
            "idx_shipment_shogun_final_upload_file_id",
            "idx_shogun_final_shipment_upload_file_id",
        ),
        # yard final
        (
            "idx_yard_shogun_final_upload_file_id",
            "idx_shogun_final_yard_upload_file_id",
        ),
    ]

    for old_idx, new_idx in index_renames:
        op.execute(
            f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM pg_indexes
                    WHERE schemaname = 'raw' AND indexname = '{old_idx}'
                ) THEN
                    ALTER INDEX raw.{old_idx} RENAME TO {new_idx};
                END IF;
            END $$;
        """
        )

    # 3. 制約名もリネーム（存在する場合）
    constraint_table_map = [
        # (old_constraint, new_constraint, table_name_after_rename)
        # receive flash
        (
            "receive_shogun_flash_pkey",
            "shogun_flash_receive_pkey",
            "shogun_flash_receive",
        ),
        (
            "receive_shogun_flash_upload_file_id_fkey",
            "shogun_flash_receive_upload_file_id_fkey",
            "shogun_flash_receive",
        ),
        # shipment flash
        (
            "shipment_shogun_flash_pkey",
            "shogun_flash_shipment_pkey",
            "shogun_flash_shipment",
        ),
        (
            "shipment_shogun_flash_upload_file_id_fkey",
            "shogun_flash_shipment_upload_file_id_fkey",
            "shogun_flash_shipment",
        ),
        # yard flash
        ("yard_shogun_flash_pkey", "shogun_flash_yard_pkey", "shogun_flash_yard"),
        (
            "yard_shogun_flash_upload_file_id_fkey",
            "shogun_flash_yard_upload_file_id_fkey",
            "shogun_flash_yard",
        ),
        # receive final
        (
            "receive_shogun_final_pkey",
            "shogun_final_receive_pkey",
            "shogun_final_receive",
        ),
        (
            "receive_shogun_final_upload_file_id_fkey",
            "shogun_final_receive_upload_file_id_fkey",
            "shogun_final_receive",
        ),
        # shipment final
        (
            "shipment_shogun_final_pkey",
            "shogun_final_shipment_pkey",
            "shogun_final_shipment",
        ),
        (
            "shipment_shogun_final_upload_file_id_fkey",
            "shogun_final_shipment_upload_file_id_fkey",
            "shogun_final_shipment",
        ),
        # yard final
        ("yard_shogun_final_pkey", "shogun_final_yard_pkey", "shogun_final_yard"),
        (
            "yard_shogun_final_upload_file_id_fkey",
            "shogun_final_yard_upload_file_id_fkey",
            "shogun_final_yard",
        ),
    ]

    for old_constraint, new_constraint, table_name in constraint_table_map:
        op.execute(
            f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = '{old_constraint}'
                    AND connamespace = 'raw'::regnamespace
                ) THEN
                    ALTER TABLE raw.{table_name}
                    RENAME CONSTRAINT {old_constraint} TO {new_constraint};
                END IF;
            END $$;
        """
        )

    print("✅ rawテーブル名をcsv_kind命名規則に統一しました")


def downgrade() -> None:
    """
    元のテーブル名に戻す
    """
    # 1. テーブルリネーム（逆順）
    renames = [
        ("shogun_flash_receive", "receive_shogun_flash"),
        ("shogun_flash_shipment", "shipment_shogun_flash"),
        ("shogun_flash_yard", "yard_shogun_flash"),
        ("shogun_final_receive", "receive_shogun_final"),
        ("shogun_final_shipment", "shipment_shogun_final"),
        ("shogun_final_yard", "yard_shogun_final"),
    ]

    for new_name, old_name in renames:
        op.execute(f"ALTER TABLE raw.{new_name} RENAME TO {old_name};")

    # 2. インデックス名も元に戻す
    index_renames = [
        (
            "idx_shogun_flash_receive_upload_file_id",
            "idx_receive_shogun_flash_upload_file_id",
        ),
        (
            "idx_shogun_flash_shipment_upload_file_id",
            "idx_shipment_shogun_flash_upload_file_id",
        ),
        (
            "idx_shogun_flash_yard_upload_file_id",
            "idx_yard_shogun_flash_upload_file_id",
        ),
        (
            "idx_shogun_final_receive_upload_file_id",
            "idx_receive_shogun_final_upload_file_id",
        ),
        (
            "idx_shogun_final_shipment_upload_file_id",
            "idx_shipment_shogun_final_upload_file_id",
        ),
        (
            "idx_shogun_final_yard_upload_file_id",
            "idx_yard_shogun_final_upload_file_id",
        ),
    ]

    for new_idx, old_idx in index_renames:
        op.execute(
            f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM pg_indexes
                    WHERE schemaname = 'raw' AND indexname = '{new_idx}'
                ) THEN
                    ALTER INDEX raw.{new_idx} RENAME TO {old_idx};
                END IF;
            END $$;
        """
        )

    print("✅ rawテーブル名を元の命名規則に戻しました")
