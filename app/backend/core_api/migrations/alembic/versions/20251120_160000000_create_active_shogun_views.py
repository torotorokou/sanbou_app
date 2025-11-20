"""create active shogun views for soft delete filtering

このマイグレーションは stg スキーマに「アクティブ行（is_deleted = false）専用ビュー」を作成します。

目的:
- 論理削除済み行を自動的に除外する共通ビューを提供
- mart スキーマのビュー/マテビューから参照することで、is_deleted 条件の書き忘れを防止

作成するビュー:
- stg.active_shogun_flash_receive
- stg.active_shogun_final_receive
- stg.active_shogun_flash_yard
- stg.active_shogun_final_yard
- stg.active_shogun_flash_shipment
- stg.active_shogun_final_shipment

各ビューは対応するテーブルから is_deleted = false の行のみを SELECT します。

Revision ID: 20251120_160000000
Revises: 20251120_150000000
Create Date: 2025-11-20 16:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "20251120_160000000"
down_revision = "20251120_150000000"
branch_labels = None
depends_on = None


# 対象となる将軍テーブル（Flash/Final × Receive/Yard/Shipment）
SHOGUN_TABLES = [
    "shogun_flash_receive",
    "shogun_flash_yard",
    "shogun_flash_shipment",
    "shogun_final_receive",
    "shogun_final_yard",
    "shogun_final_shipment",
]


def upgrade() -> None:
    """
    stg スキーマに active_* ビューを作成
    （is_deleted = false の行のみを返すフィルタビュー）
    """
    
    print("[stg.active_*] Creating active views for soft delete filtering...")
    
    for table_name in SHOGUN_TABLES:
        view_name = f"active_{table_name}"
        
        # アクティブ行専用ビューを作成
        sql = f"""
        CREATE OR REPLACE VIEW stg.{view_name} AS
        SELECT *
        FROM stg.{table_name}
        WHERE is_deleted = false;
        """
        
        op.execute(sql)
        print(f"  ✓ Created stg.{view_name}")
        
        # ビューにコメントを付与
        comment_sql = f"""
        COMMENT ON VIEW stg.{view_name} IS 
        'Active rows view: filters out soft-deleted rows (is_deleted = false only). 
        Use this view in mart aggregations to automatically exclude deleted data.';
        """
        op.execute(comment_sql)
    
    print("[stg.active_*] All active views created successfully")
    print("")
    print("📌 Next Steps:")
    print("  1. Update mart views to use stg.active_* instead of stg.* where appropriate")
    print("  2. Refresh materialized views after updating their definitions")
    print("  3. Run regression tests to verify aggregation results")


def downgrade() -> None:
    """
    active_* ビューを削除（ロールバック用）
    """
    
    print("[stg.active_*] Dropping active views...")
    
    for table_name in SHOGUN_TABLES:
        view_name = f"active_{table_name}"
        op.execute(f"DROP VIEW IF EXISTS stg.{view_name};")
        print(f"  ✓ Dropped stg.{view_name}")
    
    print("[stg.active_*] All active views dropped successfully")
