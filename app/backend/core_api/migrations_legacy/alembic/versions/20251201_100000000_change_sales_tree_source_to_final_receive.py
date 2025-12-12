"""
change_sales_tree_source_to_final_receive

このマイグレーションは、mart.v_sales_tree_detail_base ビューのデータソースを
stg.shogun_flash_receive から stg.shogun_final_receive に変更します。

変更理由:
- 最終確定データ（final_receive）を使用することで、より正確な売上分析を実現
- flash_receiveは速報データ、final_receiveは確定データ

Revision ID: 20251201_100000000
Revises: 20251128_160819394
Create Date: 2025-12-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251201_100000000'
down_revision = '20251128_160819394'
branch_labels = None
depends_on = None


def upgrade():
    """
    mart.v_sales_tree_detail_base のデータソースを
    stg.shogun_flash_receive → stg.shogun_final_receive に変更
    
    手順:
    1. 既存の mart.v_sales_tree_detail_base を DROP
    2. stg.shogun_final_receive をソースとする新しいビューを作成
    """
    print("[mart.v_sales_tree_detail_base] Changing data source to stg.shogun_final_receive...")
    
    # 1) 既存ビューをDROP
    op.execute("""
        DROP VIEW IF EXISTS mart.v_sales_tree_detail_base CASCADE;
    """)
    
    # 2) stg.shogun_final_receive をソースとする新しいビューを作成
    op.execute("""
        CREATE VIEW mart.v_sales_tree_detail_base AS
        SELECT
            COALESCE(sales_date, slip_date) AS sales_date,
            sales_staff_cd   AS rep_id,
            sales_staff_name AS rep_name,
            client_cd        AS customer_id,
            client_name      AS customer_name,
            item_cd          AS item_id,
            item_name,
            amount           AS amount_yen,
            net_weight       AS qty_kg,
            receive_no       AS slip_no,
            category_cd,
            category_name,
            CASE
                WHEN category_cd = 1 THEN 'waste'     -- 廃棄物
                WHEN category_cd = 3 THEN 'valuable'  -- 有価物
                ELSE 'other'
            END AS category_kind,
            aggregate_item_cd,
            aggregate_item_name,
            id               AS source_id,
            upload_file_id,
            source_row_no
        FROM stg.shogun_final_receive s
        WHERE
            COALESCE(sales_date, slip_date) IS NOT NULL
            AND COALESCE(is_deleted, false) = false
            AND category_cd IN (1, 3);  -- 廃棄物と有価物のみ
    """)
    
    print("[mart.v_sales_tree_detail_base] VIEW updated successfully - now using stg.shogun_final_receive.")
    
    # 3) app_readonly に SELECT 権限を付与
    print("[mart.v_sales_tree_detail_base] Granting SELECT to app_readonly...")
    op.execute("""
        GRANT SELECT ON mart.v_sales_tree_detail_base TO app_readonly;
    """)
    
    print("[mart.v_sales_tree_detail_base] Migration complete - Data source changed to stg.shogun_final_receive.")


def downgrade():
    """
    mart.v_sales_tree_detail_base を元の定義（stg.shogun_flash_receive）に戻す
    """
    print("[mart.v_sales_tree_detail_base] Reverting to stg.shogun_flash_receive...")
    
    # 1) 既存ビューをDROP
    op.execute("""
        DROP VIEW IF EXISTS mart.v_sales_tree_detail_base CASCADE;
    """)
    
    # 2) 元の定義（stg.shogun_flash_receive）に戻す
    op.execute("""
        CREATE VIEW mart.v_sales_tree_detail_base AS
        SELECT
            COALESCE(sales_date, slip_date) AS sales_date,
            sales_staff_cd   AS rep_id,
            sales_staff_name AS rep_name,
            client_cd        AS customer_id,
            client_name      AS customer_name,
            item_cd          AS item_id,
            item_name,
            amount           AS amount_yen,
            net_weight       AS qty_kg,
            receive_no       AS slip_no,
            category_cd,
            category_name,
            CASE
                WHEN category_cd = 1 THEN 'waste'
                WHEN category_cd = 3 THEN 'valuable'
                ELSE 'other'
            END AS category_kind,
            aggregate_item_cd,
            aggregate_item_name,
            id               AS source_id,
            upload_file_id,
            source_row_no
        FROM stg.shogun_flash_receive s
        WHERE
            COALESCE(sales_date, slip_date) IS NOT NULL
            AND COALESCE(is_deleted, false) = false
            AND category_cd IN (1, 3);  -- 廃棄物と有価物のみ
    """)
    
    # 3) app_readonly に SELECT 権限を付与
    op.execute("""
        GRANT SELECT ON mart.v_sales_tree_detail_base TO app_readonly;
    """)
    
    print("[mart.v_sales_tree_detail_base] Downgrade complete - Reverted to stg.shogun_flash_receive.")
