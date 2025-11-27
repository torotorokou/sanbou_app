"""rename_vendor_cd_to_vendor_id_in_stg

Revision ID: 9ea52b8773fa
Revises: 20251127_110000000
Create Date: 2025-11-27 02:18:18.851218

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251127_120000000'
down_revision = '20251127_110000000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # stg.shogun_flash_receive: vendor_cd → vendor_id
    op.execute("""
        ALTER TABLE stg.shogun_flash_receive 
        RENAME COLUMN vendor_cd TO vendor_id;
    """)
    op.execute("""
        ALTER TABLE stg.shogun_flash_receive 
        RENAME COLUMN unload_vendor_cd TO unload_vendor_id;
    """)
    op.execute("""
        ALTER TABLE stg.shogun_flash_receive 
        RENAME COLUMN transport_vendor_cd TO transport_vendor_id;
    """)
    
    # stg.shogun_final_receive: vendor_cd → vendor_id
    op.execute("""
        ALTER TABLE stg.shogun_final_receive 
        RENAME COLUMN vendor_cd TO vendor_id;
    """)
    op.execute("""
        ALTER TABLE stg.shogun_final_receive 
        RENAME COLUMN unload_vendor_cd TO unload_vendor_id;
    """)
    op.execute("""
        ALTER TABLE stg.shogun_final_receive 
        RENAME COLUMN transport_vendor_cd TO transport_vendor_id;
    """)
    
    # COMMENTを更新
    op.execute("""
        COMMENT ON COLUMN stg.shogun_flash_receive.vendor_id 
        IS '仕入先ID';
    """)
    op.execute("""
        COMMENT ON COLUMN stg.shogun_flash_receive.unload_vendor_id 
        IS '荷卸業者ID';
    """)
    op.execute("""
        COMMENT ON COLUMN stg.shogun_flash_receive.transport_vendor_id 
        IS '運搬業者ID';
    """)
    
    op.execute("""
        COMMENT ON COLUMN stg.shogun_final_receive.vendor_id 
        IS '仕入先ID';
    """)
    op.execute("""
        COMMENT ON COLUMN stg.shogun_final_receive.unload_vendor_id 
        IS '荷卸業者ID';
    """)
    op.execute("""
        COMMENT ON COLUMN stg.shogun_final_receive.transport_vendor_id 
        IS '運搬業者ID';
    """)


def downgrade() -> None:
    # COMMENTを元に戻す
    op.execute("""
        COMMENT ON COLUMN stg.shogun_final_receive.transport_vendor_id 
        IS '運搬業者CD';
    """)
    op.execute("""
        COMMENT ON COLUMN stg.shogun_final_receive.unload_vendor_id 
        IS '荷卸業者CD';
    """)
    op.execute("""
        COMMENT ON COLUMN stg.shogun_final_receive.vendor_id 
        IS '仕入先CD';
    """)
    
    op.execute("""
        COMMENT ON COLUMN stg.shogun_flash_receive.transport_vendor_id 
        IS '運搬業者CD';
    """)
    op.execute("""
        COMMENT ON COLUMN stg.shogun_flash_receive.unload_vendor_id 
        IS '荷卸業者CD';
    """)
    op.execute("""
        COMMENT ON COLUMN stg.shogun_flash_receive.vendor_id 
        IS '仕入先CD';
    """)
    
    # stg.shogun_final_receive: vendor_id → vendor_cd
    op.execute("""
        ALTER TABLE stg.shogun_final_receive 
        RENAME COLUMN transport_vendor_id TO transport_vendor_cd;
    """)
    op.execute("""
        ALTER TABLE stg.shogun_final_receive 
        RENAME COLUMN unload_vendor_id TO unload_vendor_cd;
    """)
    op.execute("""
        ALTER TABLE stg.shogun_final_receive 
        RENAME COLUMN vendor_id TO vendor_cd;
    """)
    
    # stg.shogun_flash_receive: vendor_id → vendor_cd
    op.execute("""
        ALTER TABLE stg.shogun_flash_receive 
        RENAME COLUMN transport_vendor_id TO transport_vendor_cd;
    """)
    op.execute("""
        ALTER TABLE stg.shogun_flash_receive 
        RENAME COLUMN unload_vendor_id TO unload_vendor_cd;
    """)
    op.execute("""
        ALTER TABLE stg.shogun_flash_receive 
        RENAME COLUMN vendor_id TO vendor_cd;
    """)

