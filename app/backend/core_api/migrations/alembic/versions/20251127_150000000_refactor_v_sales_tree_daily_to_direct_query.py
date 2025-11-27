"""refactor v_sales_tree_daily to direct query from stg

Revision ID: 20251127_150000000
Revises: 20251127_140000000
Create Date: 2025-11-27 15:00:00.000000

Description:
    mart.v_sales_tree_daily を mv_sales_tree_daily 経由から
    stg.shogun_flash_receive の直接クエリに変更
    
    目的:
    - マテリアライズドビューへの依存を排除
    - 常に最新データを参照可能にする
    - REFRESH 運用の制約から解放
    
    変更内容:
    - v_sales_tree_daily: FROM mart.mv_sales_tree_daily 
                       → FROM stg.shogun_flash_receive
    - カラムマッピングと WHERE 句を mv と同等に実装
    - mv_sales_tree_daily は別途運用判断（維持 or 削除）
    
    影響:
    - mart.v_sales_tree_daily のデータソースが変更される
    - インデックスの恩恵は受けられなくなる（トレードオフ）
    - v_customer_sales_daily は v_sales_tree_daily に依存するため連動
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251127_150000000'
down_revision = '20251127_140000000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Refactor v_sales_tree_daily to query stg.shogun_flash_receive directly
    """
    
    print("[mart] Recreating v_sales_tree_daily to query stg directly...")
    op.execute("DROP VIEW IF EXISTS mart.v_sales_tree_daily CASCADE")
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
        FROM stg.shogun_flash_receive
        WHERE category_cd = 1 
          AND COALESCE(sales_date, slip_date) IS NOT NULL 
          AND COALESCE(is_deleted, false) = false
    """)
    
    print("[mart] Recreating v_customer_sales_daily (dependent view)...")
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
            SUM(qty_kg) AS total_qty_kg,
            SUM(qty_kg) AS total_net_weight_kg
        FROM mart.v_sales_tree_daily v
        GROUP BY sales_date, customer_id
    """)
    
    print("[ok] v_sales_tree_daily now queries stg directly (no mv dependency)")


def downgrade() -> None:
    """
    Revert v_sales_tree_daily to query mv_sales_tree_daily
    """
    
    print("[mart] Reverting v_sales_tree_daily to query mv_sales_tree_daily...")
    op.execute("DROP VIEW IF EXISTS mart.v_sales_tree_daily CASCADE")
    op.execute("""
        CREATE VIEW mart.v_sales_tree_daily AS
        SELECT
            sales_date,
            rep_id,
            rep_name,
            customer_id,
            customer_name,
            item_id,
            item_name,
            amount_yen,
            qty_kg,
            qty_kg AS net_weight_kg,
            slip_no
        FROM mart.mv_sales_tree_daily
    """)
    
    print("[mart] Recreating v_customer_sales_daily...")
    op.execute("""
        CREATE VIEW mart.v_customer_sales_daily AS
        SELECT
            sales_date,
            customer_id,
            MAX(customer_name) AS customer_name,
            MAX(rep_id) AS rep_id,
            MAX(rep_name) AS rep_name,
            COUNT(DISTINCT slip_no) AS visit_count,
            SUM(amount_yen) AS total_amount_yen,
            SUM(qty_kg) AS total_qty_kg,
            SUM(qty_kg) AS total_net_weight_kg
        FROM mart.v_sales_tree_daily v
        GROUP BY sales_date, customer_id
    """)
    
    print("[ok] v_sales_tree_daily reverted to mv dependency")
