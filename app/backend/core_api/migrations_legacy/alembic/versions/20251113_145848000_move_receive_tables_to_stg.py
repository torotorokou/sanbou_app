"""move receive tables from raw to stg schema

このマイグレーションは以下を実行します:
1. stg スキーマを作成（存在しない場合）
2. raw.receive_shogun_flash → stg.receive_shogun_flash
3. raw.receive_shogun_final → stg.receive_shogun_final
4. raw.receive_king_final → stg.receive_king_final

既存のデータはそのまま保持され、物理的にスキーマが移動されます。
外部キー、インデックスなどもすべて維持されます。

Revision ID: 20251113_145848000
Revises: 20251106_113719410
Create Date: 2025-11-13 14:58:48.000000
"""

import sqlalchemy as sa
from alembic import context, op

# revision identifiers, used by Alembic.
revision = "20251113_145848000"
down_revision = "20251106_113719410"
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
    raw スキーマから stg スキーマへテーブルを移動
    """
    # 1. stg スキーマを作成（存在しない場合）
    op.execute("CREATE SCHEMA IF NOT EXISTS stg;")

    # 2. テーブルを raw → stg に移動
    tables_to_move = [
        "receive_shogun_flash",
        "receive_shogun_final",
        "receive_king_final",
    ]

    for table in tables_to_move:
        if _table_exists("raw", table):
            op.execute(f"ALTER TABLE raw.{table} SET SCHEMA stg;")
            print(f"✓ Moved raw.{table} → stg.{table}")
        else:
            print(f"⚠ Table raw.{table} does not exist, skipping")


def downgrade():
    """
    stg スキーマから raw スキーマへテーブルを戻す
    """
    tables_to_move = [
        "receive_shogun_flash",
        "receive_shogun_final",
        "receive_king_final",
    ]

    for table in tables_to_move:
        if _table_exists("stg", table):
            op.execute(f"ALTER TABLE stg.{table} SET SCHEMA raw;")
            print(f"✓ Moved stg.{table} → raw.{table}")
        else:
            print(f"⚠ Table stg.{table} does not exist, skipping")
