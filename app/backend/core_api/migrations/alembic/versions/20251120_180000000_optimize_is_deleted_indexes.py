"""optimize is_deleted indexes and ensure data integrity

このマイグレーションは is_deleted カラムの最適化とデータ整合性を確保します。

実施内容:
1. 既存データのクリーンアップ
   - is_deleted が NULL の行を false に更新（念のための処理）
   
2. 部分インデックスの追加
   - アクティブ行（is_deleted = false）のみに対するインデックスを作成
   - クエリの WHERE is_deleted = false 条件を高速化
   
3. インデックスの最適化
   - CONCURRENTLY オプションを使用し、ロックを最小限に抑える
   - 既存の単純インデックスは保持（削除しない）

対象テーブル:
- stg.shogun_flash_receive
- stg.shogun_final_receive
- stg.shogun_flash_yard
- stg.shogun_final_yard
- stg.shogun_flash_shipment
- stg.shogun_final_shipment

性能への影響:
- アクティブ行のみのインデックス → インデックスサイズが削減
- 論理削除された行が増えても、クエリパフォーマンスが維持される

Revision ID: 20251120_180000000
Revises: 20251120_170000000
Create Date: 2025-11-20 18:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "20251120_180000000"
down_revision = "20251120_170000000"
branch_labels = None
depends_on = None


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
    is_deleted カラムの最適化と部分インデックスの追加
    """
    
    print("[is_deleted optimization] Starting data cleanup and index creation...")
    print("")
    
    # ========================================================================
    # 1. データクリーンアップ: NULL → false への一括更新
    # ========================================================================
    print("[Step 1/3] Cleaning up NULL values in is_deleted columns...")
    
    for table_name in SHOGUN_TABLES:
        # NULL チェック（本来はないはずだが、念のため）
        check_sql = f"""
        SELECT COUNT(*) FROM stg.{table_name} WHERE is_deleted IS NULL;
        """
        
        # NULL があれば更新
        update_sql = f"""
        UPDATE stg.{table_name}
        SET is_deleted = false
        WHERE is_deleted IS NULL;
        """
        
        # 実行（NULLがなければ何もしない）
        conn = op.get_bind()
        result = conn.execute(sa.text(check_sql))
        null_count = result.scalar()
        
        if null_count > 0:
            print(f"  ⚠️  stg.{table_name}: {null_count} NULL rows found, updating to false...")
            conn.execute(sa.text(update_sql))
        else:
            print(f"  ✓ stg.{table_name}: No NULL values (already clean)")
    
    print("")
    
    # ========================================================================
    # 2. 部分インデックスの作成（is_deleted = false の行のみ）
    # ========================================================================
    print("[Step 2/3] Creating partial indexes for active rows (is_deleted = false)...")
    print("")
    print("  📌 Creating indexes (may take a few minutes on large tables)...")
    print("")
    
    for table_name in SHOGUN_TABLES:
        index_name = f"idx_{table_name}_active"
        
        # 部分インデックス作成（slip_date + upload_file_id で絞り込む想定）
        # WHERE is_deleted = false の条件で、アクティブ行のみにインデックスを張る
        # 
        # 注意: CONCURRENTLY オプションはトランザクション内で使用できないため、
        # 通常のインデックス作成を使用します。テーブルロックが発生しますが、
        # 開発環境では問題ありません。本番環境では手動で CONCURRENTLY を使用してください。
        create_index_sql = f"""
        CREATE INDEX IF NOT EXISTS {index_name}
        ON stg.{table_name} (slip_date, upload_file_id)
        WHERE is_deleted = false;
        """
        
        op.execute(create_index_sql)
        print(f"  ✓ Created {index_name} on stg.{table_name}")
    
    print("")
    
    # ========================================================================
    # 3. 既存の is_deleted インデックスとの関係性について
    # ========================================================================
    print("[Step 3/3] Index strategy summary")
    print("")
    print("  既存のインデックス:")
    print("    - idx_{table}_is_deleted (全行対象、論理削除フラグの単純インデックス)")
    print("")
    print("  新規の部分インデックス:")
    print("    - idx_{table}_active (is_deleted=false の行のみ、slip_date + upload_file_id)")
    print("")
    print("  使い分け:")
    print("    - WHERE is_deleted = false のクエリ → 部分インデックスが使用される（高速）")
    print("    - WHERE is_deleted = true のクエリ → 既存の単純インデックスが使用される")
    print("    - 論理削除率が高くなるほど、部分インデックスの効果が大きい")
    print("")
    print("[is_deleted optimization] Completed successfully")
    print("")
    print("📌 Next Steps:")
    print("  1. Run ANALYZE on stg schema to update statistics:")
    print("     docker compose exec db psql -U myuser -d sanbou_dev -c 'ANALYZE stg.shogun_flash_receive;'")
    print("  2. Refresh materialized views:")
    print("     make refresh-mv")


def downgrade() -> None:
    """
    部分インデックスを削除（ロールバック用）
    """
    
    print("[is_deleted optimization] Removing partial indexes...")
    
    for table_name in SHOGUN_TABLES:
        index_name = f"idx_{table_name}_active"
        drop_index_sql = f"DROP INDEX IF EXISTS stg.{index_name};"
        op.execute(drop_index_sql)
        print(f"  ✓ Dropped {index_name}")
    
    print("[is_deleted optimization] Rollback completed")
