"""create raw.upload_file and raw.receive_raw tables

このマイグレーションは以下を実行します:
1. raw.upload_file: CSV アップロードファイルのメタ情報を管理
   - ファイル名、ハッシュ、種別(FLASH/FINAL)、アップロード日時
   - 同一ファイルの二重取り込み防止用のユニーク制約

2. raw.receive_raw: 受入CSV の生データを行単位で保存
   - file_id (upload_file への FK)
   - row_number (CSV の行番号)
   - 各カラムは TEXT 型で CSV の生データをそのまま保存
   - 将来的に yard_raw, shipment_raw も同様の構造で作成可能

Revision ID: 20251113_150255000
Revises: 20251113_145848000
Create Date: 2025-11-13 15:02:55.000000
"""

import sqlalchemy as sa
from alembic import context, op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = "20251113_150255000"
down_revision = "20251113_145848000"
branch_labels = None
depends_on = None


def _table_exists(schema: str, table: str) -> bool:
    """
    指定されたスキーマ・テーブルが存在するかチェック
    オフラインモード（--sql）では常に False を返す
    """
    if context.is_offline_mode():
        return False
    conn = op.get_bind()
    qualified = f"{schema}.{table}"
    return bool(
        conn.scalar(sa.text("SELECT to_regclass(:q) IS NOT NULL"), {"q": qualified})
    )


def upgrade():
    """
    raw スキーマに生データ保存用テーブルを作成
    """
    # raw スキーマが存在することを確認（Step 2 で stg に移動済み）
    op.execute("CREATE SCHEMA IF NOT EXISTS raw;")

    # -------------------------------------------------------------------------
    # 1. raw.upload_file - アップロードファイルのメタ情報
    # -------------------------------------------------------------------------
    if not _table_exists("raw", "upload_file"):
        op.create_table(
            "upload_file",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("file_name", sa.Text(), nullable=False, comment="元のファイル名"),
            sa.Column(
                "file_hash", sa.String(64), nullable=False, comment="SHA-256 ハッシュ"
            ),
            sa.Column(
                "file_type", sa.String(20), nullable=False, comment="FLASH / FINAL"
            ),
            sa.Column(
                "csv_type",
                sa.String(20),
                nullable=False,
                comment="receive / yard / shipment",
            ),
            sa.Column(
                "file_size_bytes",
                sa.BigInteger(),
                nullable=True,
                comment="ファイルサイズ (bytes)",
            ),
            sa.Column(
                "row_count",
                sa.Integer(),
                nullable=True,
                comment="データ行数（ヘッダー除く）",
            ),
            sa.Column(
                "uploaded_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.Column(
                "uploaded_by",
                sa.String(100),
                nullable=True,
                comment="アップロードユーザー",
            ),
            sa.Column(
                "processing_status",
                sa.String(20),
                server_default="pending",
                nullable=False,
                comment="pending / processing / completed / failed",
            ),
            sa.Column(
                "error_message", sa.Text(), nullable=True, comment="エラーメッセージ"
            ),
            sa.Column("metadata", JSONB(), nullable=True, comment="その他のメタ情報"),
            sa.PrimaryKeyConstraint("id"),
            schema="raw",
            comment="CSV アップロードファイルのメタ情報",
        )

        # 同一ファイルの二重取り込み防止
        op.create_unique_constraint(
            "uq_upload_file_hash_type_csv",
            "upload_file",
            ["file_hash", "file_type", "csv_type"],
            schema="raw",
        )

        # インデックス作成
        op.create_index(
            "idx_upload_file_uploaded_at", "upload_file", ["uploaded_at"], schema="raw"
        )
        op.create_index(
            "idx_upload_file_status", "upload_file", ["processing_status"], schema="raw"
        )

        print("✓ Created raw.upload_file")

    # -------------------------------------------------------------------------
    # 2. raw.receive_raw - 受入CSV の生データ（行単位）
    # -------------------------------------------------------------------------
    if not _table_exists("raw", "receive_raw"):
        op.create_table(
            "receive_raw",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column(
                "file_id",
                sa.Integer(),
                nullable=False,
                comment="upload_file.id への FK",
            ),
            sa.Column(
                "row_number",
                sa.Integer(),
                nullable=False,
                comment="CSV 内の行番号（1始まり）",
            ),
            # 受入CSV の各カラム（TEXT 型で生データ保存）
            # YAML の columns 順に定義
            sa.Column("伝票日付", sa.Text(), nullable=True),
            sa.Column("売上日付", sa.Text(), nullable=True),
            sa.Column("支払日付", sa.Text(), nullable=True),
            sa.Column("業者CD", sa.Text(), nullable=True),
            sa.Column("業者名", sa.Text(), nullable=True),
            sa.Column("伝票区分CD", sa.Text(), nullable=True),
            sa.Column("伝票区分名", sa.Text(), nullable=True),
            sa.Column("品名CD", sa.Text(), nullable=True),
            sa.Column("品名", sa.Text(), nullable=True),
            sa.Column("正味重量", sa.Text(), nullable=True),
            sa.Column("数量", sa.Text(), nullable=True),
            sa.Column("単位CD", sa.Text(), nullable=True),
            sa.Column("単位名", sa.Text(), nullable=True),
            sa.Column("単価", sa.Text(), nullable=True),
            sa.Column("金額", sa.Text(), nullable=True),
            sa.Column("受入番号", sa.Text(), nullable=True),
            sa.Column("集計項目CD", sa.Text(), nullable=True),
            sa.Column("集計項目", sa.Text(), nullable=True),
            sa.Column("種類CD", sa.Text(), nullable=True),
            sa.Column("種類名", sa.Text(), nullable=True),
            sa.Column("計量時間（総重量）", sa.Text(), nullable=True),
            sa.Column("計量時間（空車重量）", sa.Text(), nullable=True),
            sa.Column("現場CD", sa.Text(), nullable=True),
            sa.Column("現場名", sa.Text(), nullable=True),
            sa.Column("荷降業者CD", sa.Text(), nullable=True),
            sa.Column("荷降業者名", sa.Text(), nullable=True),
            sa.Column("荷降現場CD", sa.Text(), nullable=True),
            sa.Column("荷降現場名", sa.Text(), nullable=True),
            sa.Column("運搬業者CD", sa.Text(), nullable=True),
            sa.Column("運搬業者名", sa.Text(), nullable=True),
            sa.Column("取引先CD", sa.Text(), nullable=True),
            sa.Column("取引先名", sa.Text(), nullable=True),
            sa.Column("マニ種類CD", sa.Text(), nullable=True),
            sa.Column("マニ種類名", sa.Text(), nullable=True),
            sa.Column("マニフェスト番号", sa.Text(), nullable=True),
            sa.Column("営業担当者CD", sa.Text(), nullable=True),
            sa.Column("営業担当者名", sa.Text(), nullable=True),
            # 追加の不明カラム（将軍CSVに存在する可能性）
            sa.Column("column38", sa.Text(), nullable=True),
            sa.Column("column39", sa.Text(), nullable=True),
            sa.Column(
                "loaded_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(
                ["file_id"],
                ["raw.upload_file.id"],
                name="fk_receive_raw_file_id",
                ondelete="CASCADE",
            ),
            schema="raw",
            comment="受入CSV の生データ（TEXT 型で保存）",
        )

        # インデックス作成
        op.create_index(
            "idx_receive_raw_file_id", "receive_raw", ["file_id"], schema="raw"
        )
        op.create_index(
            "idx_receive_raw_file_row",
            "receive_raw",
            ["file_id", "row_number"],
            unique=True,
            schema="raw",
        )

        print("✓ Created raw.receive_raw")


def downgrade():
    """
    生データテーブルを削除（FK 制約があるため順序注意）
    """
    if _table_exists("raw", "receive_raw"):
        op.drop_table("receive_raw", schema="raw")
        print("✓ Dropped raw.receive_raw")

    if _table_exists("raw", "upload_file"):
        op.drop_table("upload_file", schema="raw")
        print("✓ Dropped raw.upload_file")
