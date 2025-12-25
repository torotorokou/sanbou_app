"""normalize client_cd - 先頭0除去と末尾X除去view修正

Revision ID: 20251224_004
Revises: 20251224_003
Create Date: 2025-12-24

目的:
  stg.shogun_flash_receive / stg.shogun_final_receive の client_cd について、
  先頭の0を除去する正規化処理を実装し、既存データも backfill する。
  また、v_active_* ビューで末尾Xを除去して表示する。

原因:
  CSVアップロード時に client_cd の正規化処理が行われていなかったため、
  '001021', '00169X' のような先頭0付きのコードが残存していた。

対策:
  1. stg.normalize_client_cd() 関数の作成（冪等的な正規化ロジック）
  2. 既存データの backfill UPDATE（安全ガード付き）
  3. v_active_* ビューの修正（末尾X除去表示）

安全性:
  - client_cd は UNIQUE制約なし（重複リスクなし）
  - UPDATE 前に影響行数を出力
  - バックアップテーブル作成（ロールバック可能）
  - トランザクション内で実行
"""

from datetime import datetime

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20251224_004"
down_revision = "20251224_003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    client_cd 正規化処理の実装

    1. stg.normalize_client_cd() 関数作成
    2. バックアップテーブル作成
    3. 既存データ backfill（先頭0除去）
    4. v_active_* ビュー修正（末尾X除去表示）
    """

    print("\n" + "=" * 70)
    print("client_cd 正規化処理開始")
    print("=" * 70)

    # ========================================================================
    # 1. stg.normalize_client_cd() 関数作成
    # ========================================================================
    print("\n[1/4] 正規化関数 stg.normalize_client_cd() を作成")

    op.execute(
        """
        CREATE OR REPLACE FUNCTION stg.normalize_client_cd(input_code text)
        RETURNS text
        LANGUAGE plpgsql
        IMMUTABLE
        AS $$
        DECLARE
            trimmed text;
            result text;
        BEGIN
            -- NULL はそのまま返す
            IF input_code IS NULL THEN
                RETURN NULL;
            END IF;

            -- 前後空白を除去
            trimmed := btrim(input_code);

            -- 空文字列はそのまま返す
            IF trimmed = '' THEN
                RETURN trimmed;
            END IF;

            -- 先頭の0（半角）を除去
            -- ただし、全て0の場合は '0' を返す
            result := regexp_replace(trimmed, '^0+', '', 'g');

            -- 全て0だった場合（空文字になる）は '0' を返す
            IF result = '' THEN
                RETURN '0';
            END IF;

            RETURN result;
        END;
        $$;
    """
    )

    print("    ✓ stg.normalize_client_cd() 関数を作成しました")
    print("      - 前後空白除去")
    print("      - 先頭0除去（ただし '0000' → '0'）")
    print("      - NULL 安全")

    # ========================================================================
    # 2. バックアップテーブル作成
    # ========================================================================
    print("\n[2/4] バックアップテーブル作成")

    backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_table_flash = f"shogun_flash_receive_client_cd_backup_{backup_timestamp}"
    backup_table_final = f"shogun_final_receive_client_cd_backup_{backup_timestamp}"

    # shogun_flash_receive のバックアップ
    op.execute(
        f"""
        CREATE TABLE stg.{backup_table_flash} AS
        SELECT id, client_cd AS old_client_cd
        FROM stg.shogun_flash_receive
        WHERE btrim(client_cd) ~ '^0[0-9]';
    """
    )

    # 件数確認
    result_flash = op.get_bind().execute(
        sa.text(f"SELECT COUNT(*) FROM stg.{backup_table_flash};")
    )
    flash_backup_count = result_flash.scalar()
    print(f"    ✓ stg.{backup_table_flash}: {flash_backup_count} 件")

    # shogun_final_receive のバックアップ
    op.execute(
        f"""
        CREATE TABLE stg.{backup_table_final} AS
        SELECT id, client_cd AS old_client_cd
        FROM stg.shogun_final_receive
        WHERE btrim(client_cd) ~ '^0[0-9]';
    """
    )

    # 件数確認
    result_final = op.get_bind().execute(
        sa.text(f"SELECT COUNT(*) FROM stg.{backup_table_final};")
    )
    final_backup_count = result_final.scalar()
    print(f"    ✓ stg.{backup_table_final}: {final_backup_count} 件")

    # ========================================================================
    # 3. 既存データ backfill UPDATE
    # ========================================================================
    print("\n[3/4] 既存データ backfill UPDATE")

    # shogun_flash_receive の更新
    print("  -> stg.shogun_flash_receive を更新中...")
    result_flash_update = op.get_bind().execute(
        sa.text(
            """
        UPDATE stg.shogun_flash_receive
        SET client_cd = stg.normalize_client_cd(client_cd)
        WHERE btrim(client_cd) ~ '^0[0-9]';
    """
        )
    )
    flash_updated = result_flash_update.rowcount
    print(f"    ✓ {flash_updated} 件を更新しました")

    # shogun_final_receive の更新
    print("  -> stg.shogun_final_receive を更新中...")
    result_final_update = op.get_bind().execute(
        sa.text(
            """
        UPDATE stg.shogun_final_receive
        SET client_cd = stg.normalize_client_cd(client_cd)
        WHERE btrim(client_cd) ~ '^0[0-9]';
    """
        )
    )
    final_updated = result_final_update.rowcount
    print(f"    ✓ {final_updated} 件を更新しました")

    # ========================================================================
    # 4. v_active_* ビュー修正（末尾X除去表示）
    # ========================================================================
    print("\n[4/4] v_active_* ビュー修正（末尾X除去表示）")

    # v_active_shogun_flash_receive
    print("  -> stg.v_active_shogun_flash_receive を修正")
    op.execute(
        """
        CREATE OR REPLACE VIEW stg.v_active_shogun_flash_receive AS
        SELECT
            id,
            slip_date,
            sales_date,
            payment_date,
            vendor_cd,
            vendor_name,
            slip_type_cd,
            slip_type_name,
            item_cd,
            item_name,
            net_weight,
            quantity,
            unit_cd,
            unit_name,
            unit_price,
            amount,
            receive_no,
            aggregate_item_cd,
            aggregate_item_name,
            category_cd,
            category_name,
            weighing_time_gross,
            weighing_time_empty,
            site_cd,
            site_name,
            unload_vendor_cd,
            unload_vendor_name,
            unload_site_cd,
            unload_site_name,
            transport_vendor_cd,
            transport_vendor_name,
            regexp_replace(client_cd, '[Xx]$', '') AS client_cd,  -- 末尾X除去
            client_name,
            manifest_type_cd,
            manifest_type_name,
            manifest_no,
            sales_staff_cd,
            sales_staff_name,
            upload_file_id,
            source_row_no,
            is_deleted,
            deleted_at,
            created_at
        FROM stg.shogun_flash_receive
        WHERE is_deleted = false;
    """
    )
    print("    ✓ client_cd で末尾 X/x を除去して表示")

    # v_active_shogun_final_receive
    print("  -> stg.v_active_shogun_final_receive を修正")
    op.execute(
        """
        CREATE OR REPLACE VIEW stg.v_active_shogun_final_receive AS
        SELECT
            id,
            slip_date,
            sales_date,
            payment_date,
            vendor_cd,
            vendor_name,
            slip_type_cd,
            slip_type_name,
            item_cd,
            item_name,
            net_weight,
            quantity,
            unit_cd,
            unit_name,
            unit_price,
            amount,
            receive_no,
            aggregate_item_cd,
            aggregate_item_name,
            category_cd,
            category_name,
            weighing_time_gross,
            weighing_time_empty,
            site_cd,
            site_name,
            unload_vendor_cd,
            unload_vendor_name,
            unload_site_cd,
            unload_site_name,
            transport_vendor_cd,
            transport_vendor_name,
            regexp_replace(client_cd, '[Xx]$', '') AS client_cd,  -- 末尾X除去
            client_name,
            manifest_type_cd,
            manifest_type_name,
            manifest_no,
            sales_staff_cd,
            sales_staff_name,
            upload_file_id,
            source_row_no,
            is_deleted,
            deleted_at,
            created_at
        FROM stg.shogun_final_receive
        WHERE is_deleted = false;
    """
    )
    print("    ✓ client_cd で末尾 X/x を除去して表示")

    print("\n" + "=" * 70)
    print("client_cd 正規化処理完了")
    print("=" * 70)
    print(f"  ✓ バックアップテーブル:")
    print(f"      - stg.{backup_table_flash} ({flash_backup_count} 件)")
    print(f"      - stg.{backup_table_final} ({final_backup_count} 件)")
    print(f"  ✓ 更新件数:")
    print(f"      - shogun_flash_receive: {flash_updated} 件")
    print(f"      - shogun_final_receive: {final_updated} 件")
    print(f"  ✓ ビュー修正: 末尾X除去表示")
    print("=" * 70 + "\n")


def downgrade() -> None:
    """
    ロールバック処理

    1. v_active_* ビューを元に戻す
    2. データは元に戻さない（バックアップテーブルから手動リストア可能）
    3. 正規化関数を削除
    """

    print("\n" + "=" * 70)
    print("client_cd 正規化処理ロールバック")
    print("=" * 70)

    # ========================================================================
    # 1. v_active_* ビューを元に戻す
    # ========================================================================
    print("\n[1/2] v_active_* ビューを元の定義に戻す")

    # v_active_shogun_flash_receive
    print("  -> stg.v_active_shogun_flash_receive")
    op.execute(
        """
        CREATE OR REPLACE VIEW stg.v_active_shogun_flash_receive AS
        SELECT
            id,
            slip_date,
            sales_date,
            payment_date,
            vendor_cd,
            vendor_name,
            slip_type_cd,
            slip_type_name,
            item_cd,
            item_name,
            net_weight,
            quantity,
            unit_cd,
            unit_name,
            unit_price,
            amount,
            receive_no,
            aggregate_item_cd,
            aggregate_item_name,
            category_cd,
            category_name,
            weighing_time_gross,
            weighing_time_empty,
            site_cd,
            site_name,
            unload_vendor_cd,
            unload_vendor_name,
            unload_site_cd,
            unload_site_name,
            transport_vendor_cd,
            transport_vendor_name,
            client_cd,  -- 元に戻す（末尾X除去なし）
            client_name,
            manifest_type_cd,
            manifest_type_name,
            manifest_no,
            sales_staff_cd,
            sales_staff_name,
            upload_file_id,
            source_row_no,
            is_deleted,
            deleted_at,
            created_at
        FROM stg.shogun_flash_receive
        WHERE is_deleted = false;
    """
    )
    print("    ✓ 元の定義に戻しました")

    # v_active_shogun_final_receive
    print("  -> stg.v_active_shogun_final_receive")
    op.execute(
        """
        CREATE OR REPLACE VIEW stg.v_active_shogun_final_receive AS
        SELECT
            id,
            slip_date,
            sales_date,
            payment_date,
            vendor_cd,
            vendor_name,
            slip_type_cd,
            slip_type_name,
            item_cd,
            item_name,
            net_weight,
            quantity,
            unit_cd,
            unit_name,
            unit_price,
            amount,
            receive_no,
            aggregate_item_cd,
            aggregate_item_name,
            category_cd,
            category_name,
            weighing_time_gross,
            weighing_time_empty,
            site_cd,
            site_name,
            unload_vendor_cd,
            unload_vendor_name,
            unload_site_cd,
            unload_site_name,
            transport_vendor_cd,
            transport_vendor_name,
            client_cd,  -- 元に戻す（末尾X除去なし）
            client_name,
            manifest_type_cd,
            manifest_type_name,
            manifest_no,
            sales_staff_cd,
            sales_staff_name,
            upload_file_id,
            source_row_no,
            is_deleted,
            deleted_at,
            created_at
        FROM stg.shogun_final_receive
        WHERE is_deleted = false;
    """
    )
    print("    ✓ 元の定義に戻しました")

    # ========================================================================
    # 2. 正規化関数を削除
    # ========================================================================
    print("\n[2/2] stg.normalize_client_cd() 関数を削除")
    op.execute("DROP FUNCTION IF EXISTS stg.normalize_client_cd(text);")
    print("    ✓ 関数を削除しました")

    print("\n" + "=" * 70)
    print("ロールバック完了")
    print("=" * 70)
    print("  ⚠️  注意: 既存データは元に戻していません")
    print("      バックアップテーブル stg.shogun_*_client_cd_backup_* から")
    print("      手動でリストアできます:")
    print("")
    print("      UPDATE stg.shogun_flash_receive t")
    print("      SET client_cd = b.old_client_cd")
    print("      FROM stg.shogun_flash_receive_client_cd_backup_YYYYMMDD_HHMMSS b")
    print("      WHERE t.id = b.id;")
    print("=" * 70 + "\n")
