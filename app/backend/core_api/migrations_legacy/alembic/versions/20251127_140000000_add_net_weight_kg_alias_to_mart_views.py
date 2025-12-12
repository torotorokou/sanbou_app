"""add_net_weight_kg_alias_to_mart_views

Revision ID: 20251127_140000000
Revises: 20251127_130000000
Create Date: 2025-11-27 14:00:00.000000

Description:
    mart層のビューに net_weight_kg カラムを追加（canonical命名への移行）
    
    戦略:
    - qty_kg は後方互換性のため維持
    - net_weight_kg を追加のエイリアスとして提供
    - 両方が使用可能な状態を維持（段階的移行を可能にする）
    
    影響範囲:
    - mart.mv_sales_tree_daily (MATERIALIZED VIEW)
    - mart.v_customer_sales_daily (VIEW)
    
    目的:
    - column_naming_dictionary.md の canonical 命名規約に準拠
    - API/FE層への影響を最小化（既存の qty は継続使用可能）
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251127_140000000'
down_revision = '20251127_130000000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add net_weight_kg alias to mart views (keeping qty_kg for compatibility)
    """
    
    print("[mart] Recreating mv_sales_tree_daily with net_weight_kg alias...")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mart.mv_sales_tree_daily CASCADE")
    op.execute("""
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
            net_weight AS net_weight_kg,  -- canonical alias
            receive_no AS slip_no,
            1 AS slip_count
        FROM stg.shogun_flash_receive
        WHERE category_cd = 1
          AND COALESCE(sales_date, slip_date) IS NOT NULL
          AND COALESCE(is_deleted, false) = false
    """)
    
    print("[mart] Recreating indexes on mv_sales_tree_daily...")
    op.execute("""
        CREATE INDEX idx_mv_sales_tree_daily_composite
        ON mart.mv_sales_tree_daily (sales_date, rep_id, customer_id, item_id)
    """)
    op.execute("""
        CREATE INDEX idx_mv_sales_tree_daily_slip
        ON mart.mv_sales_tree_daily (sales_date, customer_id, slip_no)
    """)
    
    print("[mart] Recreating v_sales_tree_daily with net_weight_kg alias...")
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
            qty_kg AS net_weight_kg,  -- canonical alias
            slip_no
        FROM mart.mv_sales_tree_daily
    """)
    
    print("[mart] Recreating v_customer_sales_daily with net_weight_kg alias...")
    op.execute("DROP VIEW IF EXISTS mart.v_customer_sales_daily CASCADE")
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
            SUM(qty_kg) AS total_net_weight_kg  -- canonical alias
        FROM mart.v_sales_tree_daily v
        GROUP BY sales_date, customer_id
    """)
    
    print("[ok] Views updated with net_weight_kg alias (qty_kg maintained for compatibility)")


def downgrade() -> None:
    """
    Revert to qty_kg only (remove net_weight_kg alias)
    """
    
    print("[mart] Reverting mv_sales_tree_daily to qty_kg only...")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mart.mv_sales_tree_daily CASCADE")
    op.execute("""
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
    """)
    
    print("[mart] Recreating indexes on mv_sales_tree_daily...")
    op.execute("""
        CREATE INDEX idx_mv_sales_tree_daily_composite
        ON mart.mv_sales_tree_daily (sales_date, rep_id, customer_id, item_id)
    """)
    op.execute("""
        CREATE INDEX idx_mv_sales_tree_daily_slip
        ON mart.mv_sales_tree_daily (sales_date, customer_id, slip_no)
    """)
    
    print("[mart] Reverting v_sales_tree_daily to qty_kg only...")
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
            slip_no
        FROM mart.mv_sales_tree_daily
    """)
    
    print("[mart] Reverting v_customer_sales_daily to total_qty_kg only...")
    op.execute("DROP VIEW IF EXISTS mart.v_customer_sales_daily CASCADE")
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
            SUM(qty_kg) AS total_qty_kg
        FROM mart.v_sales_tree_daily v
        GROUP BY sales_date, customer_id
    """)
    
    print("[ok] Views reverted to qty_kg only")
