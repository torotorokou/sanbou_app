"""
use_slip_date_instead_of_coalesce

このマイグレーションは、sales-tree 関連の VIEW において、
COALESCE(sales_date, slip_date) から slip_date 単独に変更します。

変更理由:
- 日付基準を slip_date に統一し、データの一貫性を向上
- COALESCE ロジックを削除することでクエリ性能を改善
- WHERE 句の条件が単純化される

変更対象:
1. mart.v_sales_tree_detail_base (VIEW)
2. mart.mv_sales_tree_daily (MATERIALIZED VIEW)
3. sandbox.v_sales_tree_detail_base (VIEW)

影響範囲:
- 出力カラム名 'sales_date' は維持（API互換性を保つ）
- 実体として slip_date のみを使用
- mart.v_sales_tree_daily は detail_base 経由で自動反映

Revision ID: 20251201_160000000
Revises: 20251201_150000000
Create Date: 2025-12-01 16:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251201_160000000"
down_revision = "20251201_150000000"
branch_labels = None
depends_on = None


def upgrade():
    """
    sales-tree 関連 VIEW で COALESCE(sales_date, slip_date) を slip_date に変更
    """

    # ============================================================
    # 1. mart.v_sales_tree_detail_base の更新
    # ============================================================
    print("[mart.v_sales_tree_detail_base] Changing to use slip_date only...")

    op.execute(
        """
        DROP VIEW IF EXISTS mart.v_sales_tree_detail_base CASCADE;
    """
    )

    op.execute(
        """
        CREATE VIEW mart.v_sales_tree_detail_base AS
        SELECT
            slip_date AS sales_date,
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
        FROM stg.v_active_shogun_final_receive s
        WHERE
            slip_date IS NOT NULL
            AND category_cd IN (1, 3);
    """
    )

    op.execute(
        """
        GRANT SELECT ON mart.v_sales_tree_detail_base TO app_readonly;
    """
    )

    print("[mart.v_sales_tree_detail_base] Updated - now using slip_date only.")

    # ============================================================
    # 1.5. mart.v_sales_tree_daily の再作成 (detail_base を参照)
    # ============================================================
    print("[mart.v_sales_tree_daily] Recreating view (references detail_base)...")

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
            qty_kg AS net_weight_kg,
            slip_no,
            category_cd
        FROM mart.v_sales_tree_detail_base;
    """
    )

    op.execute(
        """
        GRANT SELECT ON mart.v_sales_tree_daily TO app_readonly;
    """
    )

    print("[mart.v_sales_tree_daily] Recreated - automatically uses slip_date via detail_base.")

    # ============================================================
    # 1.6. mart.v_customer_sales_daily の再作成 (v_sales_tree_daily を参照)
    # ============================================================
    print("[mart.v_customer_sales_daily] Recreating view (references v_sales_tree_daily)...")

    op.execute(
        """
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
        GROUP BY sales_date, customer_id;
    """
    )

    op.execute(
        """
        GRANT SELECT ON mart.v_customer_sales_daily TO app_readonly;
    """
    )

    print("[mart.v_customer_sales_daily] Recreated successfully.")

    # ============================================================
    # 2. mart.mv_sales_tree_daily の更新 (MATERIALIZED VIEW)
    # ============================================================
    print("[mart.mv_sales_tree_daily] Dropping and recreating with slip_date only...")

    # インデックスを明示的に削除（CASCADE で削除されるが明示）
    op.execute(
        """
        DROP INDEX IF EXISTS mart.idx_mv_sales_tree_daily_composite;
    """
    )

    op.execute(
        """
        DROP INDEX IF EXISTS mart.idx_mv_sales_tree_daily_slip;
    """
    )

    # MATERIALIZED VIEW を削除
    op.execute(
        """
        DROP MATERIALIZED VIEW IF EXISTS mart.mv_sales_tree_daily;
    """
    )

    # 新しい定義で再作成（slip_date ベース）
    op.execute(
        """
        CREATE MATERIALIZED VIEW mart.mv_sales_tree_daily AS
        SELECT
            slip_date AS sales_date,
            sales_staff_cd AS rep_id,
            sales_staff_name AS rep_name,
            client_cd AS customer_id,
            client_name AS customer_name,
            item_cd AS item_id,
            item_name,
            amount AS amount_yen,
            net_weight AS qty_kg,
            receive_no AS slip_no,
            1 AS slip_count
        FROM stg.shogun_flash_receive
        WHERE category_cd = 1
          AND slip_date IS NOT NULL
          AND COALESCE(is_deleted, false) = false
        WITH NO DATA;
    """
    )

    # インデックスを再作成
    print("[mart.mv_sales_tree_daily] Recreating indexes...")

    op.execute(
        """
        CREATE INDEX idx_mv_sales_tree_daily_composite
        ON mart.mv_sales_tree_daily (sales_date, rep_id, customer_id, item_id);
    """
    )

    op.execute(
        """
        CREATE INDEX idx_mv_sales_tree_daily_slip
        ON mart.mv_sales_tree_daily (sales_date, customer_id, slip_no);
    """
    )

    print("[mart.mv_sales_tree_daily] Updated - now using slip_date only.")
    print("[info] Run 'REFRESH MATERIALIZED VIEW mart.mv_sales_tree_daily;' to populate data.")

    # ============================================================
    # 3. sandbox.v_sales_tree_detail_base の更新
    # ============================================================
    print("[sandbox.v_sales_tree_detail_base] Changing to use slip_date only...")

    op.execute(
        """
        DROP VIEW IF EXISTS sandbox.v_sales_tree_detail_base CASCADE;
    """
    )

    op.execute(
        """
        CREATE VIEW sandbox.v_sales_tree_detail_base AS
        SELECT
            slip_date AS sales_date,
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
            slip_date IS NOT NULL
            AND COALESCE(is_deleted, false) = false;
    """
    )

    print("[sandbox.v_sales_tree_detail_base] Updated - now using slip_date only.")

    # ============================================================
    # 4. ref.v_sales_rep の再作成（CASCADE削除されたため）
    # ============================================================
    print("[ref.v_sales_rep] Recreating view (uses mart.v_sales_tree_detail_base)...")

    op.execute(
        """
        CREATE VIEW ref.v_sales_rep AS
        SELECT DISTINCT
            rep_id,
            rep_name
        FROM mart.v_sales_tree_detail_base
        ORDER BY rep_id;
    """
    )

    op.execute(
        """
        GRANT SELECT ON ref.v_sales_rep TO app_readonly;
    """
    )

    print("[ref.v_sales_rep] Recreated successfully.")

    # ============================================================
    # 5. ref.v_customer の再作成（CASCADE削除されたため）
    # ============================================================
    print("[ref.v_customer] Recreating view (uses mart.v_sales_tree_detail_base)...")

    op.execute(
        """
        CREATE VIEW ref.v_customer AS
        SELECT DISTINCT
            customer_id,
            customer_name
        FROM mart.v_sales_tree_detail_base
        ORDER BY customer_id;
    """
    )

    op.execute(
        """
        GRANT SELECT ON ref.v_customer TO app_readonly;
    """
    )

    print("[ref.v_customer] Recreated successfully.")

    # ============================================================
    # 6. ref.v_item の再作成（CASCADE削除されたため）
    # ============================================================
    print("[ref.v_item] Recreating view (uses mart.v_sales_tree_detail_base)...")

    op.execute(
        """
        CREATE VIEW ref.v_item AS
        SELECT DISTINCT
            item_id,
            item_name,
            category_cd,
            category_name
        FROM mart.v_sales_tree_detail_base
        ORDER BY item_id;
    """
    )

    op.execute(
        """
        GRANT SELECT ON ref.v_item TO app_readonly;
    """
    )

    print("[ref.v_item] Recreated successfully.")

    print("=" * 60)
    print("[OK] Migration complete - All views now use slip_date instead of COALESCE")
    print("=" * 60)


def downgrade():
    """
    sales-tree 関連 VIEW を COALESCE(sales_date, slip_date) に戻す
    """

    # ============================================================
    # 1. mart.v_sales_tree_detail_base を元に戻す
    # ============================================================
    print("[mart.v_sales_tree_detail_base] Reverting to COALESCE(sales_date, slip_date)...")

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
        FROM stg.v_active_shogun_final_receive s
        WHERE
            COALESCE(sales_date, slip_date) IS NOT NULL
            AND category_cd IN (1, 3);
    """
    )

    op.execute(
        """
        GRANT SELECT ON mart.v_sales_tree_detail_base TO app_readonly;
    """
    )

    print("[mart.v_sales_tree_detail_base] Reverted to COALESCE.")

    # ============================================================
    # 1.5. mart.v_sales_tree_daily の再作成
    # ============================================================
    print("[mart.v_sales_tree_daily] Recreating view (references detail_base)...")

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
            qty_kg AS net_weight_kg,
            slip_no,
            category_cd
        FROM mart.v_sales_tree_detail_base;
    """
    )

    op.execute(
        """
        GRANT SELECT ON mart.v_sales_tree_daily TO app_readonly;
    """
    )

    print("[mart.v_sales_tree_daily] Recreated with COALESCE via detail_base.")

    # ============================================================
    # 1.6. mart.v_customer_sales_daily の再作成
    # ============================================================
    print("[mart.v_customer_sales_daily] Recreating view (references v_sales_tree_daily)...")

    op.execute(
        """
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
        GROUP BY sales_date, customer_id;
    """
    )

    op.execute(
        """
        GRANT SELECT ON mart.v_customer_sales_daily TO app_readonly;
    """
    )

    print("[mart.v_customer_sales_daily] Recreated with COALESCE via detail_base.")

    # ============================================================
    # 2. mart.mv_sales_tree_daily を元に戻す
    # ============================================================
    print("[mart.mv_sales_tree_daily] Reverting to COALESCE(sales_date, slip_date)...")

    op.execute(
        """
        DROP INDEX IF EXISTS mart.idx_mv_sales_tree_daily_composite;
    """
    )

    op.execute(
        """
        DROP INDEX IF EXISTS mart.idx_mv_sales_tree_daily_slip;
    """
    )

    op.execute(
        """
        DROP MATERIALIZED VIEW IF EXISTS mart.mv_sales_tree_daily;
    """
    )

    op.execute(
        """
        CREATE MATERIALIZED VIEW mart.mv_sales_tree_daily AS
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
            1 AS slip_count
        FROM stg.shogun_flash_receive
        WHERE category_cd = 1
          AND COALESCE(sales_date, slip_date) IS NOT NULL
          AND COALESCE(is_deleted, false) = false
        WITH NO DATA;
    """
    )

    op.execute(
        """
        CREATE INDEX idx_mv_sales_tree_daily_composite
        ON mart.mv_sales_tree_daily (sales_date, rep_id, customer_id, item_id);
    """
    )

    op.execute(
        """
        CREATE INDEX idx_mv_sales_tree_daily_slip
        ON mart.mv_sales_tree_daily (sales_date, customer_id, slip_no);
    """
    )

    print("[mart.mv_sales_tree_daily] Reverted to COALESCE.")

    # ============================================================
    # 3. sandbox.v_sales_tree_detail_base を元に戻す
    # ============================================================
    print("[sandbox.v_sales_tree_detail_base] Reverting to COALESCE(sales_date, slip_date)...")

    op.execute(
        """
        DROP VIEW IF EXISTS sandbox.v_sales_tree_detail_base CASCADE;
    """
    )

    op.execute(
        """
        CREATE VIEW sandbox.v_sales_tree_detail_base AS
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
            AND COALESCE(is_deleted, false) = false;
    """
    )

    print("[sandbox.v_sales_tree_detail_base] Reverted to COALESCE.")

    # ============================================================
    # 4. ref.v_sales_rep の再作成
    # ============================================================
    print("[ref.v_sales_rep] Recreating view with COALESCE...")

    op.execute(
        """
        CREATE VIEW ref.v_sales_rep AS
        SELECT DISTINCT
            rep_id,
            rep_name
        FROM mart.v_sales_tree_detail_base
        ORDER BY rep_id;
    """
    )

    op.execute(
        """
        GRANT SELECT ON ref.v_sales_rep TO app_readonly;
    """
    )

    print("[ref.v_sales_rep] Recreated.")

    # ============================================================
    # 5. ref.v_customer の再作成
    # ============================================================
    print("[ref.v_customer] Recreating view with COALESCE...")

    op.execute(
        """
        CREATE VIEW ref.v_customer AS
        SELECT DISTINCT
            customer_id,
            customer_name
        FROM mart.v_sales_tree_detail_base
        ORDER BY customer_id;
    """
    )

    op.execute(
        """
        GRANT SELECT ON ref.v_customer TO app_readonly;
    """
    )

    print("[ref.v_customer] Recreated.")

    # ============================================================
    # 6. ref.v_item の再作成
    # ============================================================
    print("[ref.v_item] Recreating view with COALESCE...")

    op.execute(
        """
        CREATE VIEW ref.v_item AS
        SELECT DISTINCT
            item_id,
            item_name,
            category_cd,
            category_name
        FROM mart.v_sales_tree_detail_base
        ORDER BY item_id;
    """
    )

    op.execute(
        """
        GRANT SELECT ON ref.v_item TO app_readonly;
    """
    )

    print("[ref.v_item] Recreated.")

    print("=" * 60)
    print("[OK] Downgrade complete - All views reverted to COALESCE")
    print("=" * 60)
