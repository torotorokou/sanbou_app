"""move raw.upload_file to log.upload_file (common upload log)

このマイグレーションは raw.upload_file を log スキーマに移動し、
全 CSV アップロードの共通ログとして利用できるようにします。

変更内容:
1. log スキーマ作成（存在しない場合）
2. raw.upload_file を log.upload_file に移動
3. env カラムを追加（環境名保存用、デフォルト 'local_dev'）
4. raw.*_raw テーブルの FK を log.upload_file.id に向け直し

既存データは保持され、既存カラム（file_type, csv_type, processing_status など）はそのまま維持します。

Revision ID: 20251114_120000000
Revises: 20251114_000600000
Create Date: 2025-11-14 12:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "20251114_120000000"
down_revision = "20251114_000600000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. log スキーマ作成
    op.execute("CREATE SCHEMA IF NOT EXISTS log;")

    # 2. raw.upload_file を log スキーマに移動（既存データ・制約・インデックスはそのまま保持）
    op.execute("ALTER TABLE raw.upload_file SET SCHEMA log;")

    # 3. env カラム追加（環境名: local_dev / local_stg / vm_stg / vm_prod など）
    op.add_column(
        "upload_file",
        sa.Column("env", sa.Text(), nullable=False, server_default="local_dev"),
        schema="log",
    )

    # 4. raw.*_raw テーブルの FK を log.upload_file.id に向け直し
    #    (receive_raw, yard_raw, shipment_raw が log.upload_file を参照するように変更)

    op.drop_constraint("fk_receive_raw_file_id", "receive_raw", schema="raw", type_="foreignkey")
    op.create_foreign_key(
        "fk_receive_raw_file_id",
        "receive_raw",
        "upload_file",
        ["file_id"],
        ["id"],
        source_schema="raw",
        referent_schema="log",
        ondelete="CASCADE",
    )

    op.drop_constraint("fk_yard_raw_file_id", "yard_raw", schema="raw", type_="foreignkey")
    op.create_foreign_key(
        "fk_yard_raw_file_id",
        "yard_raw",
        "upload_file",
        ["file_id"],
        ["id"],
        source_schema="raw",
        referent_schema="log",
        ondelete="CASCADE",
    )

    op.drop_constraint("fk_shipment_raw_file_id", "shipment_raw", schema="raw", type_="foreignkey")
    op.create_foreign_key(
        "fk_shipment_raw_file_id",
        "shipment_raw",
        "upload_file",
        ["file_id"],
        ["id"],
        source_schema="raw",
        referent_schema="log",
        ondelete="CASCADE",
    )


def downgrade() -> None:
    # FK を raw.upload_file 参照に戻す
    op.drop_constraint("fk_shipment_raw_file_id", "shipment_raw", schema="raw", type_="foreignkey")
    op.create_foreign_key(
        "fk_shipment_raw_file_id",
        "shipment_raw",
        "upload_file",
        ["file_id"],
        ["id"],
        source_schema="raw",
        referent_schema="raw",
        ondelete="CASCADE",
    )

    op.drop_constraint("fk_yard_raw_file_id", "yard_raw", schema="raw", type_="foreignkey")
    op.create_foreign_key(
        "fk_yard_raw_file_id",
        "yard_raw",
        "upload_file",
        ["file_id"],
        ["id"],
        source_schema="raw",
        referent_schema="raw",
        ondelete="CASCADE",
    )

    op.drop_constraint("fk_receive_raw_file_id", "receive_raw", schema="raw", type_="foreignkey")
    op.create_foreign_key(
        "fk_receive_raw_file_id",
        "receive_raw",
        "upload_file",
        ["file_id"],
        ["id"],
        source_schema="raw",
        referent_schema="raw",
        ondelete="CASCADE",
    )

    # env カラム削除
    op.drop_column("upload_file", "env", schema="log")

    # log.upload_file を raw スキーマに戻す
    op.execute("ALTER TABLE log.upload_file SET SCHEMA raw;")
