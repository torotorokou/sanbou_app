"""add category_kind to sales_tree views

このマイグレーションは、mart.v_sales_tree_detail_base ビューを修正して
category_cd と category_kind カラムを追加し、廃棄物/有価物の両方を含めます。

変更内容:
1. mart.v_sales_tree_detail_base を DROP して再作成
   - WHERE category_cd = 1 の制限を削除
   - category_cd と category_kind カラムを追加
   - category_kind は CASE 式で 'waste' / 'valuable' に変換

これにより、フロントエンドで廃棄物/有価物タブを実装できるようになります。

Revision ID: 20251125_110000000
Revises: 20251121_100000000
Create Date: 2025-11-25 11:00:00.000000
"""

from alembic import op

revision = "20251125_110000000"
down_revision = "20251121_100000000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    mart.v_sales_tree_detail_base に category_cd と category_kind カラムを追加

    処理順序:
    1. 既存の mart.v_sales_tree_detail_base を DROP
    2. category_cd と category_kind を含む新しいビューを作成
    3. app_readonly に SELECT 権限を付与
    """

    print("[mart.v_sales_tree_detail_base] Updating VIEW to include category_kind...")

    # 1) 既存ビューをDROP
    op.execute(
        """
        DROP VIEW IF EXISTS mart.v_sales_tree_detail_base CASCADE;
    """
    )

    # 2) category_cd と category_kind を含む新しいビューを作成
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
        FROM stg.shogun_flash_receive s
        WHERE
            COALESCE(sales_date, slip_date) IS NOT NULL
            AND COALESCE(is_deleted, false) = false
            AND category_cd IN (1, 2);  -- 廃棄物と有価物のみ
    """
    )

    print("[mart.v_sales_tree_detail_base] VIEW updated successfully with category_kind.")

    # 3) app_readonly に SELECT 権限を付与
    print("[mart.v_sales_tree_detail_base] Granting SELECT to app_readonly...")

    op.execute(
        """
        GRANT SELECT ON mart.v_sales_tree_detail_base TO app_readonly;
    """
    )

    print("[mart.v_sales_tree_detail_base] Migration complete.")


def downgrade() -> None:
    """
    元の定義に戻す（廃棄物のみ、category_cd と category_kind なし）
    """

    print("[mart.v_sales_tree_detail_base] Reverting to original definition...")

    op.execute(
        """
        DROP VIEW IF EXISTS mart.v_sales_tree_detail_base CASCADE;
    """
    )

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
            category_name,
            aggregate_item_cd,
            aggregate_item_name,
            id               AS source_id,
            upload_file_id,
            source_row_no
        FROM stg.shogun_flash_receive s
        WHERE
            category_cd = 1
            AND COALESCE(sales_date, slip_date) IS NOT NULL
            AND COALESCE(is_deleted, false) = false;
    """
    )

    op.execute(
        """
        GRANT SELECT ON mart.v_sales_tree_detail_base TO app_readonly;
    """
    )

    print("[mart.v_sales_tree_detail_base] Downgrade complete.")
