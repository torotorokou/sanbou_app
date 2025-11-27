"""add upload_file_id and source_row_no to raw tables

raw層テーブルに upload_file_id と source_row_no のトラッキング機能を追加

変更内容:
1. raw.*_shogun_flash/final テーブルに upload_file_id カラム追加
2. raw.*_shogun_flash/final テーブルに source_row_no カラム追加
3. INDEX (upload_file_id) を追加

対象テーブル:
- raw.receive_shogun_flash / raw.receive_shogun_final
- raw.yard_shogun_flash / raw.yard_shogun_final
- raw.shipment_shogun_flash / raw.shipment_shogun_final

Revision ID: 20251114_130000000
Revises: 20251114_093000000
Create Date: 2025-11-14 13:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251114_130000000"
down_revision = "20251114_093000000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    raw層テーブルに upload_file_id と source_row_no を追加
    """
    
    # ========================================================================
    # raw.receive_shogun_flash
    # ========================================================================
    op.add_column(
        "receive_shogun_flash",
        sa.Column("upload_file_id", sa.Integer(), nullable=True),
        schema="raw"
    )
    
    op.add_column(
        "receive_shogun_flash",
        sa.Column("source_row_no", sa.Integer(), nullable=True),
        schema="raw"
    )
    
    op.create_index(
        "idx_receive_shogun_flash_upload_file_id",
        "receive_shogun_flash",
        ["upload_file_id"],
        schema="raw"
    )
    
    print("✓ Added upload_file_id, source_row_no to raw.receive_shogun_flash")
    
    # ========================================================================
    # raw.receive_shogun_final
    # ========================================================================
    op.add_column(
        "receive_shogun_final",
        sa.Column("upload_file_id", sa.Integer(), nullable=True),
        schema="raw"
    )
    
    op.add_column(
        "receive_shogun_final",
        sa.Column("source_row_no", sa.Integer(), nullable=True),
        schema="raw"
    )
    
    op.create_index(
        "idx_receive_shogun_final_upload_file_id",
        "receive_shogun_final",
        ["upload_file_id"],
        schema="raw"
    )
    
    print("✓ Added upload_file_id, source_row_no to raw.receive_shogun_final")
    
    # ========================================================================
    # raw.yard_shogun_flash
    # ========================================================================
    op.add_column(
        "yard_shogun_flash",
        sa.Column("upload_file_id", sa.Integer(), nullable=True),
        schema="raw"
    )
    
    op.add_column(
        "yard_shogun_flash",
        sa.Column("source_row_no", sa.Integer(), nullable=True),
        schema="raw"
    )
    
    op.create_index(
        "idx_yard_shogun_flash_upload_file_id",
        "yard_shogun_flash",
        ["upload_file_id"],
        schema="raw"
    )
    
    print("✓ Added upload_file_id, source_row_no to raw.yard_shogun_flash")
    
    # ========================================================================
    # raw.yard_shogun_final
    # ========================================================================
    op.add_column(
        "yard_shogun_final",
        sa.Column("upload_file_id", sa.Integer(), nullable=True),
        schema="raw"
    )
    
    op.add_column(
        "yard_shogun_final",
        sa.Column("source_row_no", sa.Integer(), nullable=True),
        schema="raw"
    )
    
    op.create_index(
        "idx_yard_shogun_final_upload_file_id",
        "yard_shogun_final",
        ["upload_file_id"],
        schema="raw"
    )
    
    print("✓ Added upload_file_id, source_row_no to raw.yard_shogun_final")
    
    # ========================================================================
    # raw.shipment_shogun_flash
    # ========================================================================
    op.add_column(
        "shipment_shogun_flash",
        sa.Column("upload_file_id", sa.Integer(), nullable=True),
        schema="raw"
    )
    
    op.add_column(
        "shipment_shogun_flash",
        sa.Column("source_row_no", sa.Integer(), nullable=True),
        schema="raw"
    )
    
    op.create_index(
        "idx_shipment_shogun_flash_upload_file_id",
        "shipment_shogun_flash",
        ["upload_file_id"],
        schema="raw"
    )
    
    print("✓ Added upload_file_id, source_row_no to raw.shipment_shogun_flash")
    
    # ========================================================================
    # raw.shipment_shogun_final
    # ========================================================================
    op.add_column(
        "shipment_shogun_final",
        sa.Column("upload_file_id", sa.Integer(), nullable=True),
        schema="raw"
    )
    
    op.add_column(
        "shipment_shogun_final",
        sa.Column("source_row_no", sa.Integer(), nullable=True),
        schema="raw"
    )
    
    op.create_index(
        "idx_shipment_shogun_final_upload_file_id",
        "shipment_shogun_final",
        ["upload_file_id"],
        schema="raw"
    )
    
    print("✓ Added upload_file_id, source_row_no to raw.shipment_shogun_final")


def downgrade() -> None:
    """
    追加したカラムとインデックスを削除
    """
    
    # ========================================================================
    # raw.receive_shogun_flash
    # ========================================================================
    op.drop_index("idx_receive_shogun_flash_upload_file_id", "receive_shogun_flash", schema="raw")
    op.drop_column("receive_shogun_flash", "source_row_no", schema="raw")
    op.drop_column("receive_shogun_flash", "upload_file_id", schema="raw")
    
    # ========================================================================
    # raw.receive_shogun_final
    # ========================================================================
    op.drop_index("idx_receive_shogun_final_upload_file_id", "receive_shogun_final", schema="raw")
    op.drop_column("receive_shogun_final", "source_row_no", schema="raw")
    op.drop_column("receive_shogun_final", "upload_file_id", schema="raw")
    
    # ========================================================================
    # raw.yard_shogun_flash
    # ========================================================================
    op.drop_index("idx_yard_shogun_flash_upload_file_id", "yard_shogun_flash", schema="raw")
    op.drop_column("yard_shogun_flash", "source_row_no", schema="raw")
    op.drop_column("yard_shogun_flash", "upload_file_id", schema="raw")
    
    # ========================================================================
    # raw.yard_shogun_final
    # ========================================================================
    op.drop_index("idx_yard_shogun_final_upload_file_id", "yard_shogun_final", schema="raw")
    op.drop_column("yard_shogun_final", "source_row_no", schema="raw")
    op.drop_column("yard_shogun_final", "upload_file_id", schema="raw")
    
    # ========================================================================
    # raw.shipment_shogun_flash
    # ========================================================================
    op.drop_index("idx_shipment_shogun_flash_upload_file_id", "shipment_shogun_flash", schema="raw")
    op.drop_column("shipment_shogun_flash", "source_row_no", schema="raw")
    op.drop_column("shipment_shogun_flash", "upload_file_id", schema="raw")
    
    # ========================================================================
    # raw.shipment_shogun_final
    # ========================================================================
    op.drop_index("idx_shipment_shogun_final_upload_file_id", "shipment_shogun_final", schema="raw")
    op.drop_column("shipment_shogun_final", "source_row_no", schema="raw")
    op.drop_column("shipment_shogun_final", "upload_file_id", schema="raw")
