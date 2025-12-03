"""change yard slip_no to INTEGER type

yard.slip_no は数値データなので INTEGER 型が正しい。
前回のマイグレーション (20251201_130000000) で TEXT に戻したが、
実データ確認の結果、数値のみであることが判明したため INTEGER に変更。

Revision ID: 20251201_140000000
Revises: 20251201_130000000
Create Date: 2025-12-01 14:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251201_140000000'
down_revision = '20251201_130000000'
branch_labels = None
depends_on = None


# ビュー定義（slip_no を INTEGER として扱う）
v_active_shogun_final_yard = """
CREATE OR REPLACE VIEW stg.v_active_shogun_final_yard AS
 SELECT id,
    slip_date,
    client_name,
    item_name,
    net_weight,
    quantity,
    unit_name,
    unit_price,
    amount,
    sales_staff_name,
    vendor_cd,
    vendor_name,
    category_cd,
    category_name,
    item_cd,
    slip_no,
    upload_file_id,
    source_row_no,
    is_deleted,
    deleted_at,
    created_at
   FROM stg.shogun_final_yard
  WHERE is_deleted = false;
"""

v_active_shogun_flash_yard = """
CREATE OR REPLACE VIEW stg.v_active_shogun_flash_yard AS
 SELECT id,
    slip_date,
    client_name,
    item_name,
    net_weight,
    quantity,
    unit_name,
    unit_price,
    amount,
    sales_staff_name,
    vendor_cd,
    vendor_name,
    category_cd,
    category_name,
    item_cd,
    slip_no,
    upload_file_id,
    source_row_no,
    is_deleted,
    deleted_at,
    created_at
   FROM stg.shogun_flash_yard
  WHERE is_deleted = false;
"""


def upgrade() -> None:
    """
    yard テーブルの slip_no を TEXT から INTEGER に変更
    （実データは数値のみであることを確認済み）
    """
    # ビューを削除
    op.execute("DROP VIEW IF EXISTS stg.v_active_shogun_final_yard")
    op.execute("DROP VIEW IF EXISTS stg.v_active_shogun_flash_yard")
    
    # slip_no を TEXT から INTEGER に変更
    # 空文字列やNULLは NULL に変換、数値文字列は INTEGER に変換
    op.alter_column('shogun_final_yard', 'slip_no',
               existing_type=sa.Text(),
               type_=sa.Integer(),
               postgresql_using="CASE WHEN slip_no ~ '^[0-9]+$' THEN slip_no::integer ELSE NULL END",
               schema='stg')
    
    op.alter_column('shogun_flash_yard', 'slip_no',
               existing_type=sa.Text(),
               type_=sa.Integer(),
               postgresql_using="CASE WHEN slip_no ~ '^[0-9]+$' THEN slip_no::integer ELSE NULL END",
               schema='stg')
    
    # ビューを再作成
    op.execute(v_active_shogun_final_yard)
    op.execute(v_active_shogun_flash_yard)


def downgrade() -> None:
    """
    元に戻す（TEXT型に戻す）
    """
    # ビューを削除
    op.execute("DROP VIEW IF EXISTS stg.v_active_shogun_final_yard")
    op.execute("DROP VIEW IF EXISTS stg.v_active_shogun_flash_yard")
    
    # slip_no を INTEGER から TEXT に戻す
    op.alter_column('shogun_final_yard', 'slip_no',
               existing_type=sa.Integer(),
               type_=sa.Text(),
               postgresql_using='slip_no::text',
               schema='stg')
    
    op.alter_column('shogun_flash_yard', 'slip_no',
               existing_type=sa.Integer(),
               type_=sa.Text(),
               postgresql_using='slip_no::text',
               schema='stg')
    
    # ビューを再作成
    op.execute(v_active_shogun_final_yard)
    op.execute(v_active_shogun_flash_yard)
