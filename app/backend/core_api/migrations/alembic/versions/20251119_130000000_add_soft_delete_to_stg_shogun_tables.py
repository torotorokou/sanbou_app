"""add soft delete columns to stg.*_shogun_* tables

このマイグレーションは stg 層の将軍テーブル(6テーブル)に論理削除機能を追加します。

変更内容:
- 以下の6テーブルに is_deleted, deleted_at, deleted_by カラムを追加:
  1. stg.receive_shogun_flash
  2. stg.shipment_shogun_flash
  3. stg.yard_shogun_flash
  4. stg.receive_shogun_final
  5. stg.shipment_shogun_final
  6. stg.yard_shogun_final

カラム仕様:
- is_deleted: boolean NOT NULL DEFAULT false (論理削除フラグ)
- deleted_at: timestamptz NULL (削除日時)
- deleted_by: text NULL (削除実行者)

背景:
- 日付単位での論理削除を実現し、「同一日付+種別は最後のアップロードだけ有効」を実装
- カレンダーAPIは is_deleted=false の行のみを表示
- アップロード時に既存の同日データを is_deleted=true に更新してから新規挿入

Revision ID: 20251119_130000000
Revises: 20251119_120000000
Create Date: 2025-11-19 13:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TIMESTAMP


revision = "20251119_130000000"
down_revision = "20251119_120000000"
branch_labels = None
depends_on = None


# 対象となるstg将軍テーブルのリスト
STG_SHOGUN_TABLES = [
    "receive_shogun_flash",
    "shipment_shogun_flash", 
    "yard_shogun_flash",
    "receive_shogun_final",
    "shipment_shogun_final",
    "yard_shogun_final",
]


def upgrade() -> None:
    """
    stg.*_shogun_* テーブルに論理削除カラムを追加
    """
    
    print("[stg.*_shogun_*] Adding soft delete columns to 6 tables...")
    
    for table_name in STG_SHOGUN_TABLES:
        print(f"  -> stg.{table_name}")
        
        # is_deleted カラム追加
        op.add_column(
            table_name,
            sa.Column(
                "is_deleted",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
                comment="論理削除フラグ (true=削除済み, false=有効)"
            ),
            schema="stg"
        )
        
        # deleted_at カラム追加
        op.add_column(
            table_name,
            sa.Column(
                "deleted_at",
                TIMESTAMP(timezone=True),
                nullable=True,
                comment="削除日時 (UTCタイムスタンプ)"
            ),
            schema="stg"
        )
        
        # deleted_by カラム追加
        op.add_column(
            table_name,
            sa.Column(
                "deleted_by",
                sa.Text(),
                nullable=True,
                comment="削除実行者 (ユーザー名またはシステム識別子)"
            ),
            schema="stg"
        )
        
        # インデックス作成: is_deleted でのフィルタリングを高速化
        # (upload_file_id, slip_date, is_deleted) の複合インデックス
        # ※ slip_date カラムが存在することを前提
        op.create_index(
            f"ix_{table_name}_upload_slip_deleted",
            table_name,
            ["upload_file_id", "slip_date", "is_deleted"],
            schema="stg"
        )
    
    print("[stg.*_shogun_*] Soft delete columns added successfully")


def downgrade() -> None:
    """
    論理削除カラムとインデックスを削除（ロールバック用）
    """
    
    print("[stg.*_shogun_*] Removing soft delete columns from 6 tables...")
    
    for table_name in STG_SHOGUN_TABLES:
        print(f"  -> stg.{table_name}")
        
        # インデックス削除
        op.drop_index(
            f"ix_{table_name}_upload_slip_deleted",
            table_name=table_name,
            schema="stg"
        )
        
        # カラム削除（逆順で削除）
        op.drop_column(table_name, "deleted_by", schema="stg")
        op.drop_column(table_name, "deleted_at", schema="stg")
        op.drop_column(table_name, "is_deleted", schema="stg")
    
    print("[stg.*_shogun_*] Soft delete columns removed successfully")
