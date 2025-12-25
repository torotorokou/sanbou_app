"""
use_v_active_shogun_final_receive

このマイグレーションは、mart.v_sales_tree_detail_base ビューのデータソースを
stg.shogun_final_receive から stg.v_active_shogun_final_receive に変更します。

変更理由:
- is_deleted フィルタを自動適用: ビュー層でソフトデリートが自動的に処理される
- 一貫性の向上: 他のビューと同じパターンを使用
- 保守性の向上: is_deleted フィルタがビューの定義に一元化される

変更内容:
- FROM stg.shogun_final_receive WHERE is_deleted = false
  → FROM stg.v_active_shogun_final_receive (is_deleted フィルタはビュー内で処理済み)

Revision ID: 20251201_150000000
Revises: 20251201_140000000
Create Date: 2025-12-01 15:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20251201_150000000"
down_revision = "20251201_140000000"
branch_labels = None
depends_on = None


def upgrade():
    """
    mart.v_sales_tree_detail_base のデータソースを
    stg.shogun_final_receive → stg.v_active_shogun_final_receive に変更

    手順:
    1. 既存の mart.v_sales_tree_detail_base を DROP
    2. stg.v_active_shogun_final_receive をソースとする新しいビューを作成
    """
    print(
        "[mart.v_sales_tree_detail_base] Changing data source to stg.v_active_shogun_final_receive..."
    )

    # 1) 既存ビューをDROP
    op.execute(
        """
        DROP VIEW IF EXISTS mart.v_sales_tree_detail_base CASCADE;
    """
    )

    # 2) stg.v_active_shogun_final_receive をソースとする新しいビューを作成
    # 注: is_deleted = false フィルタは不要（ビューが自動的にフィルタする）
    op.execute(
        """
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
        FROM stg.v_active_shogun_final_receive s
        WHERE
            COALESCE(sales_date, slip_date) IS NOT NULL
            AND category_cd IN (1, 3);  -- 廃棄物と有価物のみ
    """
    )

    print(
        "[mart.v_sales_tree_detail_base] VIEW updated successfully - now using stg.v_active_shogun_final_receive."
    )

    # 3) app_readonly に SELECT 権限を付与
    print("[mart.v_sales_tree_detail_base] Granting SELECT to app_readonly...")
    op.execute(
        """
        GRANT SELECT ON mart.v_sales_tree_detail_base TO app_readonly;
    """
    )

    print(
        "[mart.v_sales_tree_detail_base] Migration complete - Data source changed to stg.v_active_shogun_final_receive."
    )


def downgrade():
    """
    mart.v_sales_tree_detail_base を元の定義（stg.shogun_final_receive）に戻す
    """
    print("[mart.v_sales_tree_detail_base] Reverting to stg.shogun_final_receive...")

    # 1) 既存ビューをDROP
    op.execute(
        """
        DROP VIEW IF EXISTS mart.v_sales_tree_detail_base CASCADE;
    """
    )

    # 2) 元の定義（stg.shogun_final_receive）に戻す
    op.execute(
        """
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
        FROM stg.shogun_final_receive s
        WHERE
            COALESCE(sales_date, slip_date) IS NOT NULL
            AND COALESCE(is_deleted, false) = false
            AND category_cd IN (1, 3);  -- 廃棄物と有価物のみ
    """
    )

    # 3) app_readonly に SELECT 権限を付与
    op.execute(
        """
        GRANT SELECT ON mart.v_sales_tree_detail_base TO app_readonly;
    """
    )

    print(
        "[mart.v_sales_tree_detail_base] Downgrade complete - Reverted to stg.shogun_final_receive."
    )
