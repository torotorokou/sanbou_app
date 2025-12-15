"""create stg.yard and stg.shipment tables

YAMLの型定義に従って適切な型でカラム定義
stg層は型変換済み（INTEGER, FLOAT, TIMESTAMP等）

Revision ID: 20251113_172000000
Revises: 20251113_171000000
Create Date: 2025-11-13 17:20:00.000000
"""
from alembic import op, context
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '20251113_172000000'
down_revision = '20251113_171000000'
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
    stg スキーマに yard と shipment テーブルを作成
    """
    
    # -------------------------------------------------------------------------
    # 1. stg.yard (15カラム、型変換済み)
    # YAML yard columns 参照:
    # - 伝票日付: datetime
    # - 取引先名/品名/等: str
    # - 正味重量/数量/単価/金額: float
    # - 業者CD/種類CD/品名CD: int
    # -------------------------------------------------------------------------
    if not _table_exists("stg", "yard"):
        op.create_table(
            "yard",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("slip_date", sa.DateTime(), nullable=False, comment="伝票日付"),
            sa.Column("client_en_name", sa.Text(), nullable=False, comment="取引先名"),
            sa.Column("item_en_name", sa.Text(), nullable=False, comment="品名"),
            sa.Column("net_weight", sa.Float(), nullable=False, comment="正味重量"),
            sa.Column("quantity", sa.Float(), nullable=False, comment="数量"),
            sa.Column("unit_en_name", sa.Text(), nullable=True, comment="単位名"),
            sa.Column("unit_price", sa.Float(), nullable=True, comment="単価"),
            sa.Column("amount", sa.Float(), nullable=False, comment="金額"),
            sa.Column("sales_staff_en_name", sa.Text(), nullable=True, comment="営業担当者名"),
            sa.Column("vendor_cd", sa.Integer(), nullable=False, comment="業者CD"),
            sa.Column("vendor_en_name", sa.Text(), nullable=False, comment="業者名"),
            sa.Column("category_cd", sa.Integer(), nullable=True, comment="種類CD"),
            sa.Column("category_en_name", sa.Text(), nullable=True, comment="種類名"),
            sa.Column("item_cd", sa.Integer(), nullable=False, comment="品名CD"),
            sa.Column("slip_no", sa.Text(), nullable=True, comment="伝票番号"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            schema="stg",
            comment="ヤード一覧（整形済み）"
        )
        
        # インデックス作成
        op.create_index(
            "idx_yard_slip_date",
            "yard",
            ["slip_date"],
            schema="stg"
        )
        op.create_index(
            "idx_yard_vendor_cd",
            "yard",
            ["vendor_cd"],
            schema="stg"
        )
        
        print("✓ Created stg.yard")
    
    # -------------------------------------------------------------------------
    # 2. stg.shipment (16カラム、型変換済み)
    # YAML shipment columns 参照:
    # - 伝票日付: datetime
    # - 出荷番号/取引先名/等: str
    # - 正味重量/数量/単価/金額: float
    # - 業者CD/現場CD: int
    # -------------------------------------------------------------------------
    if not _table_exists("stg", "shipment"):
        op.create_table(
            "shipment",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("slip_date", sa.DateTime(), nullable=False, comment="伝票日付"),
            sa.Column("shipment_no", sa.Text(), nullable=False, comment="出荷番号"),
            sa.Column("client_en_name", sa.Text(), nullable=False, comment="取引先名"),
            sa.Column("vendor_cd", sa.Integer(), nullable=False, comment="業者CD"),
            sa.Column("vendor_en_name", sa.Text(), nullable=False, comment="業者名"),
            sa.Column("site_cd", sa.Integer(), nullable=True, comment="現場CD"),
            sa.Column("site_en_name", sa.Text(), nullable=True, comment="現場名"),
            sa.Column("item_en_name", sa.Text(), nullable=False, comment="品名"),
            sa.Column("net_weight", sa.Float(), nullable=False, comment="正味重量"),
            sa.Column("quantity", sa.Float(), nullable=False, comment="数量"),
            sa.Column("unit_en_name", sa.Text(), nullable=True, comment="単位名"),
            sa.Column("unit_price", sa.Float(), nullable=True, comment="単価"),
            sa.Column("amount", sa.Float(), nullable=True, comment="金額"),
            sa.Column("transport_vendor_en_name", sa.Text(), nullable=True, comment="運搬業者名"),
            sa.Column("slip_type_en_name", sa.Text(), nullable=True, comment="伝票区分名"),
            sa.Column("detail_note", sa.Text(), nullable=True, comment="明細備考"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            schema="stg",
            comment="出荷一覧（整形済み）"
        )
        
        # インデックス作成
        op.create_index(
            "idx_shipment_slip_date",
            "shipment",
            ["slip_date"],
            schema="stg"
        )
        op.create_index(
            "idx_shipment_vendor_cd",
            "shipment",
            ["vendor_cd"],
            schema="stg"
        )
        op.create_index(
            "idx_shipment_no",
            "shipment",
            ["shipment_no"],
            schema="stg"
        )
        
        print("✓ Created stg.shipment")


def downgrade():
    """
    テーブルを削除
    """
    if _table_exists("stg", "shipment"):
        op.drop_table("shipment", schema="stg")
        print("✓ Dropped stg.shipment")
    
    if _table_exists("stg", "yard"):
        op.drop_table("yard", schema="stg")
        print("✓ Dropped stg.yard")
