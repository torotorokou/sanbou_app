"""normalize_customer_id

Revision ID: 20251210_130000000
Revises: 20251202_100000000
Create Date: 2025-12-10 13:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251210_130000000"
down_revision = "20251202_100000000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Normalize customer_id by padding with zeros to 6 digits.
    This ensures consistency between Shogun Flash (000612) and Final (612) versions.
    """

    # ============================================================
    # 1. mart.v_sales_tree_detail_base の更新
    # ============================================================
    print("[mart.v_sales_tree_detail_base] Normalizing customer_id (LPAD 6 digits)...")

    # Drop dependent views first
    op.execute("DROP VIEW IF EXISTS mart.v_sales_tree_daily CASCADE;")
    op.execute("DROP VIEW IF EXISTS mart.v_sales_tree_detail_base CASCADE;")

    op.execute(
        """
        CREATE VIEW mart.v_sales_tree_detail_base AS
        SELECT
            slip_date AS sales_date,
            sales_staff_cd   AS rep_id,
            sales_staff_name AS rep_name,
            LPAD(CAST(client_cd AS TEXT), 6, '0') AS customer_id,
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

    print("[mart.v_sales_tree_detail_base] Updated - customer_id normalized.")

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

    print("[mart.v_sales_tree_daily] Recreated.")

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


def downgrade() -> None:
    """
    Revert normalization.
    """
    print("[mart.v_sales_tree_detail_base] Reverting normalization...")

    op.execute("DROP VIEW IF EXISTS mart.v_sales_tree_daily CASCADE;")
    op.execute("DROP VIEW IF EXISTS mart.v_sales_tree_detail_base CASCADE;")

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

    # Recreate dependent views (same as upgrade but with old base)
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

    print("[mart.v_sales_tree_detail_base] Reverted.")
