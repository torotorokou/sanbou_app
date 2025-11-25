"""fix category mapping waste=1 valuable=3

Revision ID: 7e3d1c5e0036
Revises: 79524e501109
Create Date: 2025-11-25 04:46:00.487125

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7e3d1c5e0036'
down_revision = '79524e501109'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    mart.v_sales_tree_detail_base のカテゴリマッピングを修正
    
    変更内容:
    - category_cd IN (1, 2) → IN (1, 3) に変更
    - category_cd = 1: 廃棄物(waste) - 処分費
    - category_cd = 3: 有価物(valuable) - 仕入
    - category_cd = 2: 運搬費は除外（売上ツリー分析対象外）
    """
    
    print("[mart.v_sales_tree_detail_base] Updating category mapping...")
    
    # ビューを再作成
    op.execute("""
        DROP VIEW IF EXISTS mart.v_sales_tree_detail_base CASCADE;
    """)
    
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
                WHEN category_cd = 1 THEN 'waste'     -- 廃棄物（処分費）
                WHEN category_cd = 3 THEN 'valuable'  -- 有価物（仕入）
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
            AND category_cd IN (1, 3);  -- 廃棄物と有価物のみ（運搬費を除外）
    """)
    
    op.execute("""
        GRANT SELECT ON mart.v_sales_tree_detail_base TO app_readonly;
    """)
    
    print("[mart.v_sales_tree_detail_base] Category mapping updated: waste=1, valuable=3")


def downgrade() -> None:
    """
    元の定義に戻す（1と2を含める）
    """
    
    print("[mart.v_sales_tree_detail_base] Reverting category mapping...")
    
    op.execute("""
        DROP VIEW IF EXISTS mart.v_sales_tree_detail_base CASCADE;
    """)
    
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
                WHEN category_cd = 2 THEN 'valuable'
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
            AND category_cd IN (1, 2);
    """)
    
    op.execute("""
        GRANT SELECT ON mart.v_sales_tree_detail_base TO app_readonly;
    """)
    
    print("[mart.v_sales_tree_detail_base] Downgrade complete.")
