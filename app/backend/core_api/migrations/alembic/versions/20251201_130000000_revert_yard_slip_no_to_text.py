"""revert yard slip_no to TEXT type

yard.slip_no には「有価物」などの文字列データが含まれるため、
INTEGER型への変更を取り消してTEXT型に戻す。

shipment.shipment_no は数値のみなのでINTEGER型のまま維持。

Revision ID: 20251201_130000000
Revises: 20251201_120000000
Create Date: 2025-12-01 13:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251201_130000000'
down_revision = '20251201_120000000'
branch_labels = None
depends_on = None


# ビュー定義（修正版: slip_no を TEXT として扱う）
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
    yard テーブルの slip_no を INTEGER から TEXT に戻す
    （「有価物」などの文字列データが含まれるため）
    """
    # ビューを削除
    op.execute("DROP VIEW IF EXISTS stg.v_active_shogun_final_yard")
    op.execute("DROP VIEW IF EXISTS stg.v_active_shogun_flash_yard")
    
    # slip_no を INTEGER から TEXT に変更
    # postgresql_using で既存の数値データを文字列に変換
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


def downgrade() -> None:
    """
    元に戻す（テスト用）
    注意: TEXT に文字列データが入っている場合、INTEGER への変換は失敗する
    """
    # ビューを削除
    op.execute("DROP VIEW IF EXISTS stg.v_active_shogun_final_yard")
    op.execute("DROP VIEW IF EXISTS stg.v_active_shogun_flash_yard")
    
    # slip_no を TEXT から INTEGER に戻す
    # 注意: 文字列データがある場合は失敗する可能性がある
    op.alter_column('shogun_final_yard', 'slip_no',
               existing_type=sa.Text(),
               type_=sa.Integer(),
               postgresql_using='CASE WHEN slip_no ~ \'^[0-9]+$\' THEN slip_no::integer ELSE NULL END',
               schema='stg')
    
    op.alter_column('shogun_flash_yard', 'slip_no',
               existing_type=sa.Text(),
               type_=sa.Integer(),
               postgresql_using='CASE WHEN slip_no ~ \'^[0-9]+$\' THEN slip_no::integer ELSE NULL END',
               schema='stg')
    
    # ビューを再作成
    op.execute(v_active_shogun_final_yard)
    op.execute(v_active_shogun_flash_yard)
