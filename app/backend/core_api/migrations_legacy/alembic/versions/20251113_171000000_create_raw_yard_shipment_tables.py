"""create raw.yard_raw and raw.shipment_raw tables

ヤードCSVと出荷CSVの生データ保存用テーブルを作成
receive_raw と同様の設計で、英語カラム名 (*_text サフィックス) を使用

Revision ID: 20251113_171000000
Revises: a4ae8a0272bd
Create Date: 2025-11-13 17:10:00.000000
"""
from alembic import op, context
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '20251113_171000000'
down_revision = '20251113_065835712'
branch_labels = None
depends_on = None


def _table_exists(schema: str, table: str) -> bool:
    """テーブルの存在確認"""
    if context.is_offline_mode():
        return False
    conn = op.get_bind()
    qualified = f"{schema}.{table}"
    return bool(conn.scalar(sa.text("SELECT to_regclass(:q) IS NOT NULL"), {"q": qualified}))


def upgrade():
    """
    yard_raw と shipment_raw テーブルを作成
    """
    
    # -------------------------------------------------------------------------
    # 1. raw.yard_raw (15カラム)
    # -------------------------------------------------------------------------
    if not _table_exists("raw", "yard_raw"):
        op.create_table(
            "yard_raw",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("file_id", sa.Integer(), nullable=False, comment="upload_file.id への FK"),
            sa.Column("row_number", sa.Integer(), nullable=False, comment="CSV 内の行番号（1始まり）"),
            
            # ヤードCSVの各カラム（TEXT型、英語名 + _text）
            sa.Column("slip_date_text", sa.Text(), nullable=True),
            sa.Column("client_name_text", sa.Text(), nullable=True),
            sa.Column("item_name_text", sa.Text(), nullable=True),
            sa.Column("net_weight_text", sa.Text(), nullable=True),
            sa.Column("quantity_text", sa.Text(), nullable=True),
            sa.Column("unit_name_text", sa.Text(), nullable=True),
            sa.Column("unit_price_text", sa.Text(), nullable=True),
            sa.Column("amount_text", sa.Text(), nullable=True),
            sa.Column("sales_staff_name_text", sa.Text(), nullable=True),
            sa.Column("vendor_cd_text", sa.Text(), nullable=True),
            sa.Column("vendor_name_text", sa.Text(), nullable=True),
            sa.Column("category_cd_text", sa.Text(), nullable=True),
            sa.Column("category_name_text", sa.Text(), nullable=True),
            sa.Column("item_cd_text", sa.Text(), nullable=True),
            sa.Column("slip_no_text", sa.Text(), nullable=True),
            
            sa.Column("loaded_at", sa.DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False),
            
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(
                ["file_id"],
                ["raw.upload_file.id"],
                name="fk_yard_raw_file_id",
                ondelete="CASCADE"
            ),
            schema="raw",
            comment="ヤードCSV の生データ（TEXT 型で保存）"
        )
        
        # インデックス作成
        op.create_index(
            "idx_yard_raw_file_id",
            "yard_raw",
            ["file_id"],
            schema="raw"
        )
        op.create_index(
            "idx_yard_raw_file_row",
            "yard_raw",
            ["file_id", "row_number"],
            unique=True,
            schema="raw"
        )
        
        print("✓ Created raw.yard_raw")
    
    # -------------------------------------------------------------------------
    # 2. raw.shipment_raw (18カラム)
    # -------------------------------------------------------------------------
    if not _table_exists("raw", "shipment_raw"):
        op.create_table(
            "shipment_raw",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("file_id", sa.Integer(), nullable=False, comment="upload_file.id への FK"),
            sa.Column("row_number", sa.Integer(), nullable=False, comment="CSV 内の行番号（1始まり）"),
            
            # 出荷CSVの各カラム（TEXT型、英語名 + _text）
            sa.Column("slip_date_text", sa.Text(), nullable=True),
            sa.Column("shipment_no_text", sa.Text(), nullable=True),
            sa.Column("client_name_text", sa.Text(), nullable=True),
            sa.Column("vendor_cd_text", sa.Text(), nullable=True),
            sa.Column("vendor_name_text", sa.Text(), nullable=True),
            sa.Column("site_cd_text", sa.Text(), nullable=True),
            sa.Column("site_name_text", sa.Text(), nullable=True),
            sa.Column("item_name_text", sa.Text(), nullable=True),
            sa.Column("net_weight_text", sa.Text(), nullable=True),
            sa.Column("quantity_text", sa.Text(), nullable=True),
            sa.Column("unit_name_text", sa.Text(), nullable=True),
            sa.Column("unit_price_text", sa.Text(), nullable=True),
            sa.Column("amount_text", sa.Text(), nullable=True),
            sa.Column("transport_vendor_name_text", sa.Text(), nullable=True),
            sa.Column("slip_type_name_text", sa.Text(), nullable=True),
            sa.Column("detail_note_text", sa.Text(), nullable=True),
            sa.Column("category_cd_text", sa.Text(), nullable=True),
            sa.Column("category_name_text", sa.Text(), nullable=True),
            
            sa.Column("loaded_at", sa.DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False),
            
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(
                ["file_id"],
                ["raw.upload_file.id"],
                name="fk_shipment_raw_file_id",
                ondelete="CASCADE"
            ),
            schema="raw",
            comment="出荷CSV の生データ（TEXT 型で保存）"
        )
        
        # インデックス作成
        op.create_index(
            "idx_shipment_raw_file_id",
            "shipment_raw",
            ["file_id"],
            schema="raw"
        )
        op.create_index(
            "idx_shipment_raw_file_row",
            "shipment_raw",
            ["file_id", "row_number"],
            unique=True,
            schema="raw"
        )
        
        print("✓ Created raw.shipment_raw")


def downgrade():
    """
    テーブルを削除
    """
    if _table_exists("raw", "shipment_raw"):
        op.drop_table("shipment_raw", schema="raw")
        print("✓ Dropped raw.shipment_raw")
    
    if _table_exists("raw", "yard_raw"):
        op.drop_table("yard_raw", schema="raw")
        print("✓ Dropped raw.yard_raw")
