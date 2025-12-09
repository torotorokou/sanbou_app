"""
refactor_ref_master_views_use_detail_base

このマイグレーションは、ref スキーマのマスタビュー（v_sales_rep, v_customer, v_item）を
stg.v_active_shogun_flash_receive から直接取得するのではなく、
mart.v_sales_tree_detail_base を経由するように変更します。

変更理由:
- 保守性の向上: すべてのマスタデータが単一のソースから派生
- 一貫性の確保: 売上データとマスタデータのソースが統一される
- データ品質: v_sales_tree_detail_base のフィルタ条件が適用される

対象ビュー:
- ref.v_sales_rep: 営業担当者マスタ
- ref.v_customer: 顧客マスタ
- ref.v_item: 品目マスタ

データ階層:
  Before: stg.v_active_shogun_flash_receive → ref.v_*
  After:  stg.shogun_final_receive → mart.v_sales_tree_detail_base → ref.v_*

Revision ID: 20251201_120000000
Revises: 20251201_110000000
Create Date: 2025-12-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251201_120000000'
down_revision = '20251201_110000000'
branch_labels = None
depends_on = None


def upgrade():
    """
    ref スキーマのマスタビューのデータソースを
    stg.v_active_shogun_flash_receive → mart.v_sales_tree_detail_base に変更
    
    利点:
    1. マスタデータと売上データのソースが統一される
    2. v_sales_tree_detail_base の変更が自動的に反映される
    3. データ品質が向上（フィルタ条件が適用される）
    """
    
    # 1) ref.v_sales_rep を更新
    print("[ref.v_sales_rep] Refactoring to use mart.v_sales_tree_detail_base...")
    op.execute("""
        DROP VIEW IF EXISTS ref.v_sales_rep CASCADE;
    """)
    op.execute("""
        CREATE VIEW ref.v_sales_rep AS
        SELECT 
            rep_id,
            MAX(rep_name) AS rep_name
        FROM mart.v_sales_tree_detail_base
        GROUP BY rep_id;
    """)
    op.execute("GRANT SELECT ON ref.v_sales_rep TO app_readonly;")
    print("[ref.v_sales_rep] Refactored successfully.")
    
    # 2) ref.v_customer を更新
    print("[ref.v_customer] Refactoring to use mart.v_sales_tree_detail_base...")
    op.execute("""
        DROP VIEW IF EXISTS ref.v_customer CASCADE;
    """)
    op.execute("""
        CREATE VIEW ref.v_customer AS
        SELECT 
            customer_id,
            MAX(customer_name) AS customer_name,
            MAX(rep_id) AS rep_id,
            MAX(rep_name) AS rep_name
        FROM mart.v_sales_tree_detail_base
        GROUP BY customer_id;
    """)
    op.execute("GRANT SELECT ON ref.v_customer TO app_readonly;")
    print("[ref.v_customer] Refactored successfully.")
    
    # 3) ref.v_item を更新
    print("[ref.v_item] Refactoring to use mart.v_sales_tree_detail_base...")
    op.execute("""
        DROP VIEW IF EXISTS ref.v_item CASCADE;
    """)
    op.execute("""
        CREATE VIEW ref.v_item AS
        SELECT 
            item_id,
            MAX(item_name) AS item_name,
            NULL::integer AS unit_cd,
            NULL::text AS unit_name,
            MAX(category_cd) AS category_cd,
            MAX(category_name) AS category_name
        FROM mart.v_sales_tree_detail_base
        GROUP BY item_id;
    """)
    op.execute("GRANT SELECT ON ref.v_item TO app_readonly;")
    print("[ref.v_item] Refactored successfully.")
    
    print("[ref] All master views refactored - Data source unified.")


def downgrade():
    """
    ref スキーマのマスタビューを元の定義（stg.v_active_shogun_flash_receive）に戻す
    """
    
    # 1) ref.v_sales_rep を元に戻す
    print("[ref.v_sales_rep] Reverting to stg.v_active_shogun_flash_receive...")
    op.execute("""
        DROP VIEW IF EXISTS ref.v_sales_rep CASCADE;
    """)
    op.execute("""
        CREATE VIEW ref.v_sales_rep AS
        SELECT 
            sales_staff_cd AS rep_id,
            MAX(sales_staff_name) AS rep_name
        FROM stg.v_active_shogun_flash_receive s
        GROUP BY sales_staff_cd;
    """)
    op.execute("GRANT SELECT ON ref.v_sales_rep TO app_readonly;")
    
    # 2) ref.v_customer を元に戻す
    print("[ref.v_customer] Reverting to stg.v_active_shogun_flash_receive...")
    op.execute("""
        DROP VIEW IF EXISTS ref.v_customer CASCADE;
    """)
    op.execute("""
        CREATE VIEW ref.v_customer AS
        SELECT 
            client_cd AS customer_id,
            MAX(client_name) AS customer_name,
            MAX(sales_staff_cd) AS rep_id,
            MAX(sales_staff_name) AS rep_name
        FROM stg.v_active_shogun_flash_receive s
        GROUP BY client_cd;
    """)
    op.execute("GRANT SELECT ON ref.v_customer TO app_readonly;")
    
    # 3) ref.v_item を元に戻す
    print("[ref.v_item] Reverting to stg.v_active_shogun_flash_receive...")
    op.execute("""
        DROP VIEW IF EXISTS ref.v_item CASCADE;
    """)
    op.execute("""
        CREATE VIEW ref.v_item AS
        SELECT 
            item_cd AS item_id,
            MAX(item_name) AS item_name,
            MAX(unit_cd) AS unit_cd,
            MAX(unit_name) AS unit_name,
            MAX(category_cd) AS category_cd,
            MAX(category_name) AS category_name
        FROM stg.v_active_shogun_flash_receive s
        GROUP BY item_cd;
    """)
    op.execute("GRANT SELECT ON ref.v_item TO app_readonly;")
    
    print("[ref] Downgrade complete - Reverted to stg.v_active_shogun_flash_receive.")
