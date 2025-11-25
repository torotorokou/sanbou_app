"""move sales tree views from sandbox to mart

このマイグレーションは、sandbox スキーマにある売上ツリー関連ビューを
mart スキーマに移行します。

背景:
- 現在、sandbox.v_sales_tree_detail_base および sandbox.v_sales_tree_daily が
  試験的に sandbox スキーマに配置されている
- 実運用で使用するため、これらを mart スキーマに移動する

移行対象ビュー:
1. sandbox.v_sales_tree_detail_base → mart.v_sales_tree_detail_base
   - stg.shogun_flash_receive から集計
   - 日付×営業×顧客×商品の詳細データ

2. sandbox.v_sales_tree_daily → mart.v_sales_tree_daily
   - 現状は sandbox.mv_sales_tree_daily を参照
   - (mv_sales_tree_daily の移行は将来の別revisionで実施)

互換性方針:
- 旧 sandbox.* ビューは残したまま運用（互換期間）
- アプリケーションコードを mart.* に切り替え後、
  別revisionで sandbox 側をDROPする

権限:
- app_user に SELECT 権限を付与

Revision ID: 20251125_100000000
Revises: 20251121_100000000
Create Date: 2025-11-25 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "20251125_100000000"
down_revision = "20251121_100000000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    mart スキーマに売上ツリービューを作成
    
    処理順序:
    1. 既存の mart.v_sales_tree_* をDROP（再実行でも安全）
    2. mart.v_sales_tree_detail_base を作成
    3. mart.v_sales_tree_daily を作成
    4. app_user に SELECT 権限を付与
    
    注意:
    - sandbox 側のビューは削除しない（互換期間として残す）
    """
    
    print("[mart.v_sales_tree_detail_base] Creating VIEW for sales tree detail data...")
    
    # 1) 既存ビューをDROP（再実行時の安全性確保）
    op.execute("""
        DROP VIEW IF EXISTS mart.v_sales_tree_detail_base CASCADE;
    """)
    
    op.execute("""
        DROP VIEW IF EXISTS mart.v_sales_tree_daily CASCADE;
    """)
    
    # 2) mart.v_sales_tree_detail_base を作成
    # stg.shogun_flash_receive から売上データを抽出
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
    """)
    
    print("[mart.v_sales_tree_detail_base] VIEW created successfully.")
    
    # 3) mart.v_sales_tree_daily を作成
    # 現状は sandbox.mv_sales_tree_daily を参照（将来的に mart 側に移行予定）
    print("[mart.v_sales_tree_daily] Creating VIEW for daily aggregated sales tree data...")
    
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
            slip_count
        FROM sandbox.mv_sales_tree_daily;
    """)
    
    print("[mart.v_sales_tree_daily] VIEW created successfully.")
    
    # 4) app_readonly に SELECT 権限を付与（app_user は存在しない場合があるため app_readonly を使用）
    print("[mart.v_sales_tree_*] Granting SELECT to app_readonly...")
    
    op.execute("""
        GRANT SELECT ON mart.v_sales_tree_detail_base TO app_readonly;
    """)
    
    op.execute("""
        GRANT SELECT ON mart.v_sales_tree_daily TO app_readonly;
    """)
    
    print("[mart.v_sales_tree_*] Permissions granted successfully.")
    
    # NOTE:
    # 旧 sandbox.v_sales_tree_detail_base / sandbox.v_sales_tree_daily は
    # いきなり DROP せず、そのまま残す。
    # アプリケーションコードを mart.* に切り替えた後、
    # 別 revision で sandbox 側を DROP する。
    print("[INFO] sandbox.v_sales_tree_* views remain intact for compatibility.")


def downgrade() -> None:
    """
    mart スキーマのビューを削除
    
    注意:
    - sandbox 側のビューは元々存在していたものとして、
      ここでは再作成しない（既存のものをそのまま使う前提）
    """
    
    print("[mart.v_sales_tree_*] Dropping VIEWs...")
    
    op.execute("""
        DROP VIEW IF EXISTS mart.v_sales_tree_daily CASCADE;
    """)
    
    op.execute("""
        DROP VIEW IF EXISTS mart.v_sales_tree_detail_base CASCADE;
    """)
    
    print("[mart.v_sales_tree_*] VIEWs dropped successfully.")
    
    # NOTE:
    # sandbox 側のビューは downgrade でも削除しない。
    # 元々存在していたものとして扱う。
