"""revert_vendor_id_to_vendor_cd_in_stg

このマイグレーションは 20251127_120000000 で誤って変更されたカラム名を元に戻します。

背景:
  - raw / stg レイヤでは vendor_cd / vendor_name を「正」とする設計
  - 20251127_120000000 で誤って vendor_cd → vendor_id に変更された
  - YAML と Python コードは vendor_cd を前提としているため INSERT が失敗
  
修正内容:
  - stg.shogun_flash_receive: vendor_id → vendor_cd に戻す
  - stg.shogun_final_receive: vendor_id → vendor_cd に戻す
  - 同様に unload_vendor_id, transport_vendor_id も元に戻す

設計方針の再確認:
  - raw / stg: vendor_cd (固定)
  - mart 以降: 必要に応じて vendor_id などに翻訳可能

Revision ID: 20251127_180000000
Revises: 20251127_170000000
Create Date: 2025-11-27 18:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251127_180000000'
down_revision = '20251127_170000000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    stg 層のカラム名を vendor_id → vendor_cd に戻す
    """
    print("[stg.shogun_flash_receive] Reverting vendor_id → vendor_cd...")
    
    # stg.shogun_flash_receive: vendor_id → vendor_cd
    op.execute("""
        ALTER TABLE stg.shogun_flash_receive 
        RENAME COLUMN vendor_id TO vendor_cd;
    """)
    op.execute("""
        ALTER TABLE stg.shogun_flash_receive 
        RENAME COLUMN unload_vendor_id TO unload_vendor_cd;
    """)
    op.execute("""
        ALTER TABLE stg.shogun_flash_receive 
        RENAME COLUMN transport_vendor_id TO transport_vendor_cd;
    """)
    
    print("[stg.shogun_final_receive] Reverting vendor_id → vendor_cd...")
    
    # stg.shogun_final_receive: vendor_id → vendor_cd
    op.execute("""
        ALTER TABLE stg.shogun_final_receive 
        RENAME COLUMN vendor_id TO vendor_cd;
    """)
    op.execute("""
        ALTER TABLE stg.shogun_final_receive 
        RENAME COLUMN unload_vendor_id TO unload_vendor_cd;
    """)
    op.execute("""
        ALTER TABLE stg.shogun_final_receive 
        RENAME COLUMN transport_vendor_id TO transport_vendor_cd;
    """)
    
    print("[COMMENT] Updating column comments...")
    
    # COMMENTを元に戻す (CD が正しい表記)
    op.execute("""
        COMMENT ON COLUMN stg.shogun_flash_receive.vendor_cd 
        IS '業者コード - 取引先業者の識別コード';
    """)
    op.execute("""
        COMMENT ON COLUMN stg.shogun_flash_receive.unload_vendor_cd 
        IS '荷卸業者コード - 荷卸し作業を行う業者の識別コード';
    """)
    op.execute("""
        COMMENT ON COLUMN stg.shogun_flash_receive.transport_vendor_cd 
        IS '運搬業者コード - 運搬を行う業者の識別コード';
    """)
    
    op.execute("""
        COMMENT ON COLUMN stg.shogun_final_receive.vendor_cd 
        IS '業者コード - 取引先業者の識別コード';
    """)
    op.execute("""
        COMMENT ON COLUMN stg.shogun_final_receive.unload_vendor_cd 
        IS '荷卸業者コード - 荷卸し作業を行う業者の識別コード';
    """)
    op.execute("""
        COMMENT ON COLUMN stg.shogun_final_receive.transport_vendor_cd 
        IS '運搬業者コード - 運搬を行う業者の識別コード';
    """)
    
    print("[VIEW] Updating stg.v_active_shogun_flash_receive...")
    
    # ビュー stg.v_active_shogun_flash_receive を更新（エイリアス不要になる）
    op.execute("""
        CREATE OR REPLACE VIEW stg.v_active_shogun_flash_receive AS
        SELECT 
            id,
            slip_date,
            sales_date,
            payment_date,
            vendor_cd,              -- AS 不要
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
            unload_vendor_cd,       -- AS 不要
            unload_vendor_name,
            unload_site_cd,
            unload_site_name,
            transport_vendor_cd,    -- AS 不要
            transport_vendor_name,
            client_cd,
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
    """)
    
    print("[VIEW] Updating stg.v_active_shogun_final_receive...")
    
    # ビュー stg.v_active_shogun_final_receive も更新
    op.execute("""
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
            client_cd,
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
    """)
    
    print("✅ Reverted all vendor_id columns to vendor_cd in stg schema")


def downgrade() -> None:
    """
    ロールバック: vendor_cd → vendor_id に戻す
    （ただし、これは設計的に望ましくない状態に戻すことになる）
    """
    print("[WARNING] Downgrading will restore the problematic vendor_id naming...")
    
    # ビューを元に戻す（エイリアス付き）
    op.execute("""
        CREATE OR REPLACE VIEW stg.v_active_shogun_final_receive AS
        SELECT 
            id,
            slip_date,
            sales_date,
            payment_date,
            vendor_id AS vendor_cd,
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
            unload_vendor_id AS unload_vendor_cd,
            unload_vendor_name,
            unload_site_cd,
            unload_site_name,
            transport_vendor_id AS transport_vendor_cd,
            transport_vendor_name,
            client_cd,
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
    """)
    
    op.execute("""
        CREATE OR REPLACE VIEW stg.v_active_shogun_flash_receive AS
        SELECT 
            id,
            slip_date,
            sales_date,
            payment_date,
            vendor_id AS vendor_cd,
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
            unload_vendor_id AS unload_vendor_cd,
            unload_vendor_name,
            unload_site_cd,
            unload_site_name,
            transport_vendor_id AS transport_vendor_cd,
            transport_vendor_name,
            client_cd,
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
    """)
    
    # COMMENTを戻す
    op.execute("""
        COMMENT ON COLUMN stg.shogun_final_receive.transport_vendor_cd 
        IS '運搬業者ID';
    """)
    op.execute("""
        COMMENT ON COLUMN stg.shogun_final_receive.unload_vendor_cd 
        IS '荷卸業者ID';
    """)
    op.execute("""
        COMMENT ON COLUMN stg.shogun_final_receive.vendor_cd 
        IS '仕入先ID';
    """)
    
    op.execute("""
        COMMENT ON COLUMN stg.shogun_flash_receive.transport_vendor_cd 
        IS '運搬業者ID';
    """)
    op.execute("""
        COMMENT ON COLUMN stg.shogun_flash_receive.unload_vendor_cd 
        IS '荷卸業者ID';
    """)
    op.execute("""
        COMMENT ON COLUMN stg.shogun_flash_receive.vendor_cd 
        IS '仕入先ID';
    """)
    
    # stg.shogun_final_receive: vendor_cd → vendor_id
    op.execute("""
        ALTER TABLE stg.shogun_final_receive 
        RENAME COLUMN transport_vendor_cd TO transport_vendor_id;
    """)
    op.execute("""
        ALTER TABLE stg.shogun_final_receive 
        RENAME COLUMN unload_vendor_cd TO unload_vendor_id;
    """)
    op.execute("""
        ALTER TABLE stg.shogun_final_receive 
        RENAME COLUMN vendor_cd TO vendor_id;
    """)
    
    # stg.shogun_flash_receive: vendor_cd → vendor_id
    op.execute("""
        ALTER TABLE stg.shogun_flash_receive 
        RENAME COLUMN transport_vendor_cd TO transport_vendor_id;
    """)
    op.execute("""
        ALTER TABLE stg.shogun_flash_receive 
        RENAME COLUMN unload_vendor_cd TO unload_vendor_id;
    """)
    op.execute("""
        ALTER TABLE stg.shogun_flash_receive 
        RENAME COLUMN vendor_cd TO vendor_id;
    """)
    
    print("⚠️  Downgrade complete (reverted to vendor_id naming)")
