"""
refactor_v_sales_tree_daily_use_detail_base

このマイグレーションは、mart.v_sales_tree_daily を
stg.v_active_shogun_flash_receive から直接取得するのではなく、
mart.v_sales_tree_detail_base を経由するように変更します。

変更理由:
- 保守性の向上: データソースが一元化され、変更が容易になる
- 一貫性の確保: v_sales_tree_detail_base が唯一のデータソースとなる
- 将来の変更への対応: v_sales_tree_detail_base の変更が自動的に反映される

データ階層:
  Before: stg.v_active_shogun_flash_receive → mart.v_sales_tree_daily
  After:  stg.shogun_final_receive → mart.v_sales_tree_detail_base → mart.v_sales_tree_daily

Revision ID: 20251201_110000000
Revises: 20251201_100000000
Create Date: 2025-12-01 11:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251201_110000000"
down_revision = "20251201_100000000"
branch_labels = None
depends_on = None


def upgrade():
    """
    mart.v_sales_tree_daily のデータソースを
    stg.v_active_shogun_flash_receive → mart.v_sales_tree_detail_base に変更

    利点:
    1. データソースの一元化
    2. mart.v_sales_tree_detail_base の変更が自動的に反映される
    3. 保守性が向上（データソース変更時の修正箇所が減る）
    """
    print(
        "[mart.v_sales_tree_daily] Refactoring to use mart.v_sales_tree_detail_base..."
    )

    # 1) 既存ビューをDROP
    op.execute(
        """
        DROP VIEW IF EXISTS mart.v_sales_tree_daily CASCADE;
    """
    )

    # 2) mart.v_sales_tree_detail_base をソースとする新しいビューを作成
    # category_kind は不要（v_sales_tree_detail_base で既にフィルタ済み）
    op.execute(
        """
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
            qty_kg AS net_weight_kg,  -- エイリアス（後方互換性）
            slip_no,
            category_cd
        FROM mart.v_sales_tree_detail_base;
    """
    )

    print(
        "[mart.v_sales_tree_daily] VIEW refactored - now using mart.v_sales_tree_detail_base."
    )

    # 3) app_readonly に SELECT 権限を付与
    print("[mart.v_sales_tree_daily] Granting SELECT to app_readonly...")
    op.execute(
        """
        GRANT SELECT ON mart.v_sales_tree_daily TO app_readonly;
    """
    )

    print("[mart.v_sales_tree_daily] Migration complete - Data source unified.")


def downgrade():
    """
    mart.v_sales_tree_daily を元の定義（stg.v_active_shogun_flash_receive）に戻す
    """
    print("[mart.v_sales_tree_daily] Reverting to stg.v_active_shogun_flash_receive...")

    # 1) 既存ビューをDROP
    op.execute(
        """
        DROP VIEW IF EXISTS mart.v_sales_tree_daily CASCADE;
    """
    )

    # 2) 元の定義（stg.v_active_shogun_flash_receive）に戻す
    op.execute(
        """
        CREATE VIEW mart.v_sales_tree_daily AS
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
        WHERE (category_cd = ANY (ARRAY[1, 3]))
          AND COALESCE(sales_date, slip_date) IS NOT NULL;
    """
    )

    # 3) app_readonly に SELECT 権限を付与
    op.execute(
        """
        GRANT SELECT ON mart.v_sales_tree_daily TO app_readonly;
    """
    )

    print(
        "[mart.v_sales_tree_daily] Downgrade complete - Reverted to stg.v_active_shogun_flash_receive."
    )
