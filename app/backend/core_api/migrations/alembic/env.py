# /backend/migrations/alembic/env.py
# ------------------------------------------------------------
# Alembic 環境設定（FastAPI + SQLAlchemy 2.0 / psycopg3 想定）
# - DSN: DB_DSN または DATABASE_URL を環境変数から取得
# - postgresql:// → postgresql+psycopg:// に自動補正（psycopg3）
# - 複数スキーマ（raw/ref/mart）差分検出: include_schemas=True
# - 型/デフォルト値の差分検出: compare_type / compare_server_default
# - プロジェクト直下 (/backend) を sys.path に追加して import 解決
# ------------------------------------------------------------
from __future__ import annotations

import os
import sys
from pathlib import Path
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ------------------------------------------------------------
# ロギング設定
# ------------------------------------------------------------
config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

# ------------------------------------------------------------
# sys.path に /backend を追加（app.* を import できるように）
# このファイルの位置: /backend/migrations/alembic/env.py
# parents[2] = /backend
# ------------------------------------------------------------
BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.append(str(BACKEND_ROOT))

# あなたの SQLAlchemy Base を import
from app.infra.db.orm_models import Base  # noqa: E402

# Alembic が参照するメタデータ（オートジェネレートの基準）
target_metadata = Base.metadata


def _get_url() -> str:
    """
    優先順:
      1) DB_DSN
      2) DATABASE_URL
    psycopg3 を使う場合は postgresql+psycopg:// に正規化する。
    """
    url = os.getenv("DB_DSN") or os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("Set DB_DSN or DATABASE_URL")

    # psycopg3 を明示（psycopg2 を使う場合はこの補正を無効化する）
    if url.startswith("postgresql://") and "+psycopg" not in url and "+psycopg2" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _configure_context_offline(url: str) -> None:
    """
    オフラインモード(接続せずにSQL生成)設定
    """
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        version_table="alembic_version",
        version_table_schema="public",
        include_schemas=True,          # 複数スキーマの差分を含める
        compare_type=True,             # 型の差分検出
        compare_server_default=True,   # サーバデフォルトの差分検出
    )


def _configure_context_online(url: str):
    """
    オンラインモード(実DBに接続して実行)設定
    """
    connectable = engine_from_config(
        {"sqlalchemy.url": url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,  # SQLAlchemy 2.x
    )
    connection = connectable.connect()
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table="alembic_version",
        version_table_schema="public",
        include_schemas=True,          # 複数スキーマの差分を含める
        compare_type=True,             # 型の差分検出
        compare_server_default=True,   # サーバデフォルトの差分検出
    )
    return connectable, connection


def run_migrations_offline() -> None:
    """'offline' モード: DB接続なしにマイグレーションを生成"""
    url = _get_url()
    _configure_context_offline(url)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """'online' モード: 実DBに接続してマイグレーションを適用"""
    url = _get_url()
    connectable, connection = _configure_context_online(url)
    try:
        with context.begin_transaction():
            context.run_migrations()
    finally:
        # 明示的にクローズ
        connection.close()
        connectable.dispose()


# ------------------------------------------------------------
# メインディスパッチ: offline / online の分岐
# ------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
