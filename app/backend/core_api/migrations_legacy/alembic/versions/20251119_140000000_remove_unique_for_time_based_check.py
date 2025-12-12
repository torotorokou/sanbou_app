"""remove unique constraint for time-based duplicate check

このマイグレーションは log.upload_file の UNIQUE 制約を完全に削除します。

変更内容:
- 部分ユニークインデックス ux_upload_file_hash_type_csv_status_active を削除
- 代わりにアプリケーション側で「直近N分以内の同一ファイル」のみを重複とする

背景:
- 同じファイルでも時間をおいて再アップロードすることを許可
- 短時間（デフォルト3分）での連続アップロードのみ 409 エラーにする
- UX 改善: 誤操作防止と柔軟な再アップロードの両立

Revision ID: 20251119_140000000
Revises: 20251119_130000000
Create Date: 2025-11-19 14:00:00.000000
"""
from alembic import op


revision = "20251119_140000000"
down_revision = "20251119_130000000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    部分ユニークインデックスを削除し、アプリケーション側でチェックに移行
    """
    
    print("[log.upload_file] Removing partial unique index for time-based duplicate check...")
    
    # 部分ユニークインデックスを削除（存在する場合のみ）
    op.execute(
        "DROP INDEX IF EXISTS log.ux_upload_file_hash_type_csv_status_active;"
    )
    print("✓ Dropped partial unique index: ux_upload_file_hash_type_csv_status_active")
    print("  - Duplicate check now handled by application layer")
    print("  - Only recent uploads (within N minutes) will be rejected")
    
    # 通常のインデックス（検索用）を作成
    # uploaded_at を含めて「直近N分以内の検索」を高速化
    op.create_index(
        "ix_upload_file_hash_csv_time",
        "upload_file",
        ["file_hash", "csv_type", "uploaded_by", "uploaded_at"],
        schema="log"
    )
    print("✓ Created search index: ix_upload_file_hash_csv_time")
    print("  - Optimizes time-based duplicate checks")


def downgrade() -> None:
    """
    通常のインデックスを削除し、部分ユニークインデックスを復元
    """
    
    print("[log.upload_file] Restoring partial unique index...")
    
    # 検索用インデックスを削除
    op.drop_index(
        "ix_upload_file_hash_csv_time",
        table_name="upload_file",
        schema="log"
    )
    print("✓ Dropped search index: ix_upload_file_hash_csv_time")
    
    # 部分ユニークインデックスを復元
    op.execute(
        """
        CREATE UNIQUE INDEX ux_upload_file_hash_type_csv_status_active
        ON log.upload_file (file_hash, file_type, csv_type, processing_status)
        WHERE is_deleted = false;
        """
    )
    print("✓ Restored partial unique index: ux_upload_file_hash_type_csv_status_active")
