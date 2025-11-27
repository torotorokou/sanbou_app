"""replace unique constraint with partial unique index for soft delete

このマイグレーションは log.upload_file の UNIQUE 制約を部分ユニークインデックスに置き換えます。

変更内容:
- 既存制約 uq_upload_file_hash_type_csv_status を削除
- 新規部分ユニークインデックス ux_upload_file_hash_type_csv_status_active を追加
  - WHERE is_deleted = false 条件付き
  - is_deleted=true のレコードは制約から除外される

背景:
- 論理削除されたレコードは重複チェック対象外とする
- is_deleted=false のレコードのみユニーク制約を適用
- これにより、削除後の同一CSVの再アップロードが可能になる

技術詳細:
- PostgreSQL の部分インデックス（Partial Index）機能を利用
- 部分ユニークインデックスは WHERE 句の条件を満たすレコードのみに適用される

Revision ID: 20251119_110000000
Revises: 20251119_100000000
Create Date: 2025-11-19 11:00:00.000000
"""
from alembic import op


revision = "20251119_110000000"
down_revision = "20251119_100000000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    UNIQUE 制約を部分ユニークインデックスに置き換え
    """
    
    print("[log.upload_file] Replacing UNIQUE constraint with partial unique index...")
    
    # 既存の UNIQUE 制約を削除
    op.drop_constraint(
        "uq_upload_file_hash_type_csv_status",
        "upload_file",
        schema="log",
        type_="unique"
    )
    print("✓ Dropped existing unique constraint: uq_upload_file_hash_type_csv_status")
    
    # 部分ユニークインデックスを作成（is_deleted=false のみに適用）
    op.execute(
        """
        CREATE UNIQUE INDEX ux_upload_file_hash_type_csv_status_active
        ON log.upload_file (file_hash, file_type, csv_type, processing_status)
        WHERE is_deleted = false;
        """
    )
    print("✓ Created partial unique index: ux_upload_file_hash_type_csv_status_active")
    print("  - Applies only to records where is_deleted = false")
    print("  - Allows re-uploading same CSV after soft deletion")


def downgrade() -> None:
    """
    部分ユニークインデックスを削除し、元の UNIQUE 制約を復元
    """
    
    # 部分ユニークインデックスを削除
    op.execute(
        "DROP INDEX IF EXISTS log.ux_upload_file_hash_type_csv_status_active;"
    )
    print("✓ Dropped partial unique index: ux_upload_file_hash_type_csv_status_active")
    
    # 元の UNIQUE 制約を復元
    op.create_unique_constraint(
        "uq_upload_file_hash_type_csv_status",
        "upload_file",
        ["file_hash", "file_type", "csv_type", "processing_status"],
        schema="log"
    )
    print("✓ Restored unique constraint: uq_upload_file_hash_type_csv_status")
