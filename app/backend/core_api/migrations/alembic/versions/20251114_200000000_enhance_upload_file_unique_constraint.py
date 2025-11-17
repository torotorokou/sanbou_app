"""enhance upload_file unique constraint with processing_status

log.upload_file の UNIQUE 制約を強化し、並行リクエストによる重複挿入を防止

変更内容:
- 既存制約 uq_upload_file_hash_type_csv (file_hash, file_type, csv_type) を削除
- 新規制約 uq_upload_file_hash_type_csv_status (file_hash, file_type, csv_type, processing_status) を追加
- これにより、pending と success で同じハッシュを許可しつつ、同じ状態での重複を防ぐ

背景:
- 並行リクエストで重複チェックをすり抜けるレースコンディションを DB 層で防止
- processing_status = 'success' のファイルのみを重複対象とするロジックを DB 制約でサポート

Revision ID: 20251114_200000000
Revises: 20251114_add_shipment_category
Create Date: 2025-11-14 20:00:00.000000
"""
from alembic import op

revision = "20251114_200000000"
down_revision = "20251114_add_shipment_category"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    UNIQUE 制約を processing_status を含む形に強化
    """
    
    print("[log.upload_file] Enhancing UNIQUE constraint with processing_status...")
    
    # 既存の制約を削除
    op.drop_constraint(
        "uq_upload_file_hash_type_csv",
        "upload_file",
        schema="log",
        type_="unique"
    )
    
    # 新しい制約を追加（processing_status を含む）
    op.create_unique_constraint(
        "uq_upload_file_hash_type_csv_status",
        "upload_file",
        ["file_hash", "file_type", "csv_type", "processing_status"],
        schema="log"
    )
    
    print("✓ Enhanced UNIQUE constraint: uq_upload_file_hash_type_csv_status")


def downgrade() -> None:
    """
    元の制約に戻す
    """
    op.drop_constraint(
        "uq_upload_file_hash_type_csv_status",
        "upload_file",
        schema="log",
        type_="unique"
    )
    
    op.create_unique_constraint(
        "uq_upload_file_hash_type_csv",
        "upload_file",
        ["file_hash", "file_type", "csv_type"],
        schema="log"
    )
