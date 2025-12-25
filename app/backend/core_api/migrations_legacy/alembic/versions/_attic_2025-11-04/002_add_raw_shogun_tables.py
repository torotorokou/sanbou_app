"""Add raw schema for shogun CSV tables (generated from YAML) - ARCHIVED

【アーカイブ理由】
DBにベースライン未刻印のため未適用。
新運用では単一ベースライン(9a092c4a1fcf)から再構築するため、このリビジョンは使用しません。
参照・検証目的でのみ保全しています。

Revision ID: 002
Revises: 001
Create Date: 2025-10-27 00:00:00

このマイグレーションは shogun_csv_masters.yaml から動的に生成されます。
YAMLファイルが唯一の真(Single Source of Truth)です。
"""

import os
import sys

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# app.config モジュールをインポートパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from app.config.table_definition import get_table_definition_generator

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """YAMLから動的にテーブルを生成"""
    # テーブル定義ジェネレーターを取得
    generator = get_table_definition_generator()

    # Create raw schema
    op.execute("CREATE SCHEMA IF NOT EXISTS raw")

    # CSV種別ごとにテーブルを作成
    for csv_type in generator.get_csv_types():
        table_name = f"{csv_type}_shogun_flash"
        columns_def = generator.get_columns_definition(csv_type)

        # カラム定義を構築
        columns = [
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        ]

        # YAMLからカラムを追加
        for col in columns_def:
            col_type = (
                getattr(sa, col["type"])()
                if col["type"] in ["String", "Integer", "Numeric", "Boolean"]
                else sa.Date()
            )
            columns.append(
                sa.Column(
                    col["en_name"],
                    col_type,
                    nullable=col["nullable"],
                    comment=col["comment"],
                )
            )

        # 共通カラムを追加
        columns.extend(
            [
                sa.Column(
                    "raw_data_json",
                    postgresql.JSONB(astext_type=sa.Text()),
                    nullable=True,
                    comment="元データJSON",
                ),
                sa.Column(
                    "uploaded_at",
                    sa.TIMESTAMP(),
                    nullable=False,
                    server_default=sa.text("NOW()"),
                    comment="アップロード日時",
                ),
                sa.Column(
                    "created_at",
                    sa.TIMESTAMP(),
                    nullable=False,
                    server_default=sa.text("NOW()"),
                    comment="作成日時",
                ),
                sa.PrimaryKeyConstraint("id"),
            ]
        )

        # テーブル作成
        op.create_table(table_name, *columns, schema="raw")

        # インデックス作成
        index_columns = generator.generate_index_columns(csv_type)
        for idx_col in index_columns:
            index_name = f"ix_raw_{csv_type}_{idx_col}"
            op.create_index(index_name, table_name, [idx_col], unique=False, schema="raw")


def downgrade() -> None:
    """テーブルとスキーマを削除"""
    generator = get_table_definition_generator()

    for csv_type in generator.get_csv_types():
        table_name = f"{csv_type}_shogun_flash"
        op.drop_table(table_name, schema="raw")

    op.execute("DROP SCHEMA IF EXISTS raw CASCADE")
