"""add category_cd to v_sales_tree_daily

Revision ID: 20251127_170000000
Revises: 20251127_160000000
Create Date: 2025-11-27 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251127_170000000'
down_revision = '20251127_160000000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    mart.v_sales_tree_daily に category_cd カラムを追加
    
    目的:
    - 廃棄物 (category_cd=1) と有価物 (category_cd=3) の両方を含める
    - category_cd カラムで区別可能にする
    
    影響範囲:
    - mart.v_customer_sales_daily: 依存ビューだが、必要なカラムのみ明示的に指定しているため影響なし
    - 既存コード: SELECT * を使用していないため後方互換性あり
    
    変更内容:
    - 11列 → 12列 (category_cd を最後に追加)
    """
    
    print("[mart.v_sales_tree_daily] Adding category_cd column...")
    
    # 1. 依存ビューを CASCADE で DROP
    op.execute("DROP VIEW IF EXISTS mart.v_customer_sales_daily CASCADE")
    
    # 2. mart.v_sales_tree_daily を再作成（category_cd 追加 + 有価物含む）
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_sales_tree_daily AS
        SELECT
            COALESCE(sales_date, slip_date) AS sales_date,
            sales_staff_cd AS rep_id,
            sales_staff_name AS rep_name,
            client_cd AS customer_id,
            client_name AS customer_name,
            item_cd AS item_id,
            item_name,
            amount AS amount_yen,
            net_weight AS qty_kg,
            net_weight AS net_weight_kg,
            receive_no AS slip_no,
            category_cd
        FROM stg.v_active_shogun_flash_receive
        WHERE category_cd IN (1, 3)
          AND COALESCE(sales_date, slip_date) IS NOT NULL
    """)
    
    # 3. mart.v_customer_sales_daily を再作成（依存ビュー）
    print("[mart.v_customer_sales_daily] Recreating dependent view...")
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_customer_sales_daily AS
        SELECT
            sales_date,
            customer_id,
            MAX(customer_name) AS customer_name,
            MAX(rep_id) AS rep_id,
            MAX(rep_name) AS rep_name,
            COUNT(DISTINCT slip_no) AS visit_count,
            SUM(amount_yen) AS total_amount_yen,
            SUM(qty_kg) AS total_qty_kg
        FROM mart.v_sales_tree_daily v
        GROUP BY sales_date, customer_id
    """)
    
    print("[ok] category_cd added to mart.v_sales_tree_daily (12 columns)")


def downgrade() -> None:
    """
    Revert to 11-column version without category_cd
    """
    print("[mart.v_sales_tree_daily] Removing category_cd column...")
    
    # 1. 依存ビューを CASCADE で DROP
    op.execute("DROP VIEW IF EXISTS mart.v_customer_sales_daily CASCADE")
    
    # 2. mart.v_sales_tree_daily を元に戻す（11列）
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_sales_tree_daily AS
        SELECT
            COALESCE(sales_date, slip_date) AS sales_date,
            sales_staff_cd AS rep_id,
            sales_staff_name AS rep_name,
            client_cd AS customer_id,
            client_name AS customer_name,
            item_cd AS item_id,
            item_name,
            amount AS amount_yen,
            net_weight AS qty_kg,
            net_weight AS net_weight_kg,
            receive_no AS slip_no
        FROM stg.v_active_shogun_flash_receive
        WHERE category_cd = 1
          AND COALESCE(sales_date, slip_date) IS NOT NULL
    """)
    
    # 3. mart.v_customer_sales_daily を再作成
    print("[mart.v_customer_sales_daily] Recreating dependent view...")
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_customer_sales_daily AS
        SELECT
            sales_date,
            customer_id,
            MAX(customer_name) AS customer_name,
            MAX(rep_id) AS rep_id,
            MAX(rep_name) AS rep_name,
            COUNT(DISTINCT slip_no) AS visit_count,
            SUM(amount_yen) AS total_amount_yen,
            SUM(qty_kg) AS total_qty_kg
        FROM mart.v_sales_tree_daily v
        GROUP BY sales_date, customer_id
    """)
    
    print("[ok] Reverted to 11-column version")
