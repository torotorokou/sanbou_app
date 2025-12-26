"""add upload_file_id and source_row_no to stg tables

stg層テーブルに upload_file_id と source_row_no のトラッキング機能を追加

変更内容:
1. stg.*_shogun_* テーブルに upload_file_id, source_row_no カラムを追加
2. INDEX (upload_file_id, source_row_no) を追加

対象テーブル:
- stg.receive_shogun_flash / yard_shogun_flash / shipment_shogun_flash
- stg.receive_shogun_final / yard_shogun_final / shipment_shogun_final

既存データ対応:
- server_default='0' で既存行に 0 を設定
- 新規データは UseCase 側で正しい値を設定

Revision ID: 20251114_130100000
Revises: 20251114_130000000
Create Date: 2025-11-14 13:01:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20251114_130100000"
down_revision = "20251114_130000000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    stg層テーブルに upload_file_id, source_row_no カラムとINDEXを追加
    """

    tables = [
        "receive_shogun_flash",
        "yard_shogun_flash",
        "shipment_shogun_flash",
        "receive_shogun_final",
        "yard_shogun_final",
        "shipment_shogun_final",
    ]

    for table in tables:
        print(f"[{table}] Adding upload_file_id and source_row_no columns...")

        # カラム追加（nullable=True で既存コードとの互換性を保つ）
        op.add_column(
            table,
            sa.Column(
                "upload_file_id",
                sa.Integer(),
                nullable=True,
                comment="アップロード元ファイル ID (log.upload_file.id への参照)",
            ),
            schema="stg",
        )

        op.add_column(
            table,
            sa.Column(
                "source_row_no",
                sa.Integer(),
                nullable=True,
                comment="CSV元行番号（1-indexed）",
            ),
            schema="stg",
        )

        # INDEX作成（upload_file_id, source_row_no の複合インデックス）
        op.create_index(
            f"idx_{table}_upload",
            table,
            ["upload_file_id", "source_row_no"],
            schema="stg",
        )

        print(f"✓ Updated stg.{table}: added upload_file_id, source_row_no, and index")


def downgrade() -> None:
    """
    カラムとINDEXを削除
    """

    tables = [
        "receive_shogun_flash",
        "yard_shogun_flash",
        "shipment_shogun_flash",
        "receive_shogun_final",
        "yard_shogun_final",
        "shipment_shogun_final",
    ]

    for table in tables:
        op.drop_index(f"idx_{table}_upload", table, schema="stg")
        op.drop_column(table, "source_row_no", schema="stg")
        op.drop_column(table, "upload_file_id", schema="stg")
