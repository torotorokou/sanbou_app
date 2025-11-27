"""refactor all views to use v_active_shogun_flash_receive

Revision ID: 20251127_160000000
Revises: 20251127_150000000
Create Date: 2025-11-27 16:00:00.000000

Description:
    全ての業務ロジック用ビューを stg.v_active_shogun_flash_receive 参照に統一
    
    目的:
    - 論理削除フラグ (is_deleted) の一元管理
    - stg.shogun_flash_receive の直接参照を廃止
    - WHERE is_deleted = false の冗長な記述を削除
    
    変更対象:
    1. mart.v_sales_tree_daily (VIEW)
    2. mart.v_sales_tree_detail_base (VIEW)
    3. ref.v_customer (VIEW)
    4. ref.v_item (VIEW)
    5. ref.v_sales_rep (VIEW)
    
    備考:
    - mart.mv_sales_tree_daily は削除予定のため対象外
    - Python コードは別途手動で修正が必要
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251127_160000000'
down_revision = '20251127_150000000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Refactor all business logic views to use stg.v_active_shogun_flash_receive
    """
    
    # 1. mart.v_sales_tree_daily
    print("[mart.v_sales_tree_daily] Refactoring to use v_active...")
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
        FROM stg.v_active_shogun_flash_receive
        WHERE category_cd = 1 
          AND COALESCE(sales_date, slip_date) IS NOT NULL
    """)
    
    # 2. mart.v_customer_sales_daily を再作成（依存ビュー）
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
            SUM(qty_kg) AS total_qty_kg,
            SUM(qty_kg) AS total_net_weight_kg
        FROM mart.v_sales_tree_daily v
        GROUP BY sales_date, customer_id
    """)
    
    # 3. mart.v_sales_tree_detail_base
    print("[mart.v_sales_tree_detail_base] Refactoring to use v_active...")
    op.execute("DROP VIEW IF EXISTS mart.v_sales_tree_detail_base CASCADE")
    op.execute("""
        CREATE OR REPLACE VIEW mart.v_sales_tree_detail_base AS
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
            receive_no AS slip_no,
            category_cd,
            category_name,
            CASE
                WHEN (category_cd = 1) THEN 'waste'::text
                WHEN (category_cd = 3) THEN 'valuable'::text
                ELSE 'other'::text
            END AS category_kind,
            aggregate_item_cd,
            aggregate_item_name,
            id AS source_id,
            upload_file_id,
            source_row_no
        FROM stg.v_active_shogun_flash_receive s
        WHERE COALESCE(sales_date, slip_date) IS NOT NULL
          AND category_cd = ANY (ARRAY[1, 3])
    """)
    
    # 4. ref.v_customer
    print("[ref.v_customer] Refactoring to use v_active...")
    op.execute("DROP VIEW IF EXISTS ref.v_customer CASCADE")
    op.execute("""
        CREATE OR REPLACE VIEW ref.v_customer AS
        SELECT 
            client_cd AS customer_id,
            MAX(client_name) AS customer_name,
            MAX(sales_staff_cd) AS rep_id,
            MAX(sales_staff_name) AS rep_name
        FROM stg.v_active_shogun_flash_receive s
        GROUP BY client_cd
    """)
    
    # 5. ref.v_item
    print("[ref.v_item] Refactoring to use v_active...")
    op.execute("DROP VIEW IF EXISTS ref.v_item CASCADE")
    op.execute("""
        CREATE OR REPLACE VIEW ref.v_item AS
        SELECT 
            item_cd AS item_id,
            MAX(item_name) AS item_name,
            MAX(unit_cd) AS unit_cd,
            MAX(unit_name) AS unit_name,
            MAX(category_cd) AS category_cd,
            MAX(category_name) AS category_name
        FROM stg.v_active_shogun_flash_receive s
        GROUP BY item_cd
    """)
    
    # 6. ref.v_sales_rep
    print("[ref.v_sales_rep] Refactoring to use v_active...")
    op.execute("DROP VIEW IF EXISTS ref.v_sales_rep CASCADE")
    op.execute("""
        CREATE OR REPLACE VIEW ref.v_sales_rep AS
        SELECT 
            sales_staff_cd AS rep_id,
            MAX(sales_staff_name) AS rep_name
        FROM stg.v_active_shogun_flash_receive s
        GROUP BY sales_staff_cd
    """)
    
    print("[ok] All views refactored to use stg.v_active_shogun_flash_receive")
    print("[info] Python code still needs manual update:")
    print("  - app/infra/adapters/upload/raw_data_repository.py")
    print("  - app/presentation/routers/database/router.py")


def downgrade() -> None:
    """
    Revert all views to use stg.shogun_flash_receive with is_deleted filter
    """
    
    # 1. mart.v_sales_tree_daily
    print("[mart.v_sales_tree_daily] Reverting to stg.shogun_flash_receive...")
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
    
    # 2. mart.v_customer_sales_daily
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
    
    # 3. mart.v_sales_tree_detail_base
    print("[mart.v_sales_tree_detail_base] Reverting...")
    op.execute("DROP VIEW IF EXISTS mart.v_sales_tree_detail_base CASCADE")
    op.execute("""
        CREATE VIEW mart.v_sales_tree_detail_base AS
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
            receive_no AS slip_no,
            category_cd,
            category_name,
            CASE
                WHEN (category_cd = 1) THEN 'waste'::text
                WHEN (category_cd = 3) THEN 'valuable'::text
                ELSE 'other'::text
            END AS category_kind,
            aggregate_item_cd,
            aggregate_item_name,
            id AS source_id,
            upload_file_id,
            source_row_no
        FROM stg.shogun_flash_receive s
        WHERE COALESCE(sales_date, slip_date) IS NOT NULL
          AND COALESCE(is_deleted, false) = false
          AND category_cd = ANY (ARRAY[1, 3])
    """)
    
    # 4. ref.v_customer
    print("[ref.v_customer] Reverting...")
    op.execute("DROP VIEW IF EXISTS ref.v_customer CASCADE")
    op.execute("""
        CREATE VIEW ref.v_customer AS
        SELECT 
            client_cd AS customer_id,
            MAX(client_name) AS customer_name,
            MAX(sales_staff_cd) AS rep_id,
            MAX(sales_staff_name) AS rep_name
        FROM stg.shogun_flash_receive s
        WHERE is_deleted = false
        GROUP BY client_cd
    """)
    
    # 5. ref.v_item
    print("[ref.v_item] Reverting...")
    op.execute("DROP VIEW IF EXISTS ref.v_item CASCADE")
    op.execute("""
        CREATE VIEW ref.v_item AS
        SELECT 
            item_cd AS item_id,
            MAX(item_name) AS item_name,
            MAX(unit_cd) AS unit_cd,
            MAX(unit_name) AS unit_name,
            MAX(category_cd) AS category_cd,
            MAX(category_name) AS category_name
        FROM stg.shogun_flash_receive s
        WHERE is_deleted = false
        GROUP BY item_cd
    """)
    
    # 6. ref.v_sales_rep
    print("[ref.v_sales_rep] Reverting...")
    op.execute("DROP VIEW IF EXISTS ref.v_sales_rep CASCADE")
    op.execute("""
        CREATE VIEW ref.v_sales_rep AS
        SELECT 
            sales_staff_cd AS rep_id,
            MAX(sales_staff_name) AS rep_name
        FROM stg.shogun_flash_receive s
        WHERE is_deleted = false
        GROUP BY sales_staff_cd
    """)
    
    print("[ok] All views reverted to stg.shogun_flash_receive")
