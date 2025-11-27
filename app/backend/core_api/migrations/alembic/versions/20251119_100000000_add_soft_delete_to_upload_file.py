"""add soft delete columns to log.upload_file

このマイグレーションは log.upload_file に論理削除機能を追加します。

変更内容:
1. is_deleted: 論理削除フラグ (boolean NOT NULL DEFAULT false)
2. deleted_at: 削除日時 (timestamptz NULL)
3. deleted_by: 削除実行者 (text NULL)

背景:
- カレンダーUIから「削除」操作を行った場合、物理削除ではなく is_deleted=true に更新
- 削除されたレコードは重複チェックから除外され、同じCSVの再アップロードが可能になる
- stg 集計ビューも is_deleted=false のデータのみをカウントする

Revision ID: 20251119_100000000
Revises: 20251117_135913797
Create Date: 2025-11-19 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TIMESTAMP


revision = "20251119_100000000"
down_revision = "20251117_135913797"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    log.upload_file に論理削除カラムを追加
    """
    
    print("[log.upload_file] Adding soft delete columns...")
    
    # is_deleted カラム追加
    op.add_column(
        "upload_file",
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment="論理削除フラグ (true=削除済み, false=有効)"
        ),
        schema="log"
    )
    
    # deleted_at カラム追加
    op.add_column(
        "upload_file",
        sa.Column(
            "deleted_at",
            TIMESTAMP(timezone=True),
            nullable=True,
            comment="削除日時 (is_deleted=true の場合に設定)"
        ),
        schema="log"
    )
    
    # deleted_by カラム追加
    op.add_column(
        "upload_file",
        sa.Column(
            "deleted_by",
            sa.Text(),
            nullable=True,
            comment="削除実行者（ユーザー名など）"
        ),
        schema="log"
    )
    
    print("✓ Added is_deleted, deleted_at, deleted_by columns to log.upload_file")


def downgrade() -> None:
    """
    論理削除カラムを削除
    """
    op.drop_column("upload_file", "deleted_by", schema="log")
    op.drop_column("upload_file", "deleted_at", schema="log")
    op.drop_column("upload_file", "is_deleted", schema="log")
    
    print("✓ Dropped soft delete columns from log.upload_file")
