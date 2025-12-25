"""add indexes for duplicate upload check

log.upload_file にフォールバック用の複合インデックスを追加

変更内容:
- フォールバック用インデックス: (csv_type, file_name, file_size_bytes, row_count, processing_status)
- 既存の UNIQUE制約 (file_hash, file_type, csv_type) で第一候補のクエリはカバー済み

重複チェックのクエリパターン:
1. 第一候補: WHERE csv_type = ? AND file_hash = ? AND processing_status = 'success'
   → 既存UNIQUE制約でカバー (uq_upload_file_hash_type_csv)

2. フォールバック: WHERE csv_type = ? AND file_name = ? AND file_size_bytes = ?
                    AND row_count = ? AND processing_status = 'success'
   → このマイグレーションで追加

Revision ID: 20251114_130200000
Revises: 20251114_130100000
Create Date: 2025-11-14 13:02:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251114_130200000"
down_revision = "20251114_130100000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    重複チェック用のフォールバックインデックスを追加
    """

    print("[log.upload_file] Creating duplicate check fallback index...")

    # フォールバック用: (csv_type, file_name, file_size_bytes, row_count, processing_status)
    op.create_index(
        "idx_upload_file_duplicate_fallback",
        "upload_file",
        ["csv_type", "file_name", "file_size_bytes", "row_count", "processing_status"],
        schema="log",
    )

    print("✓ Created idx_upload_file_duplicate_fallback on log.upload_file")


def downgrade() -> None:
    """
    インデックスを削除
    """
    op.drop_index("idx_upload_file_duplicate_fallback", "upload_file", schema="log")
