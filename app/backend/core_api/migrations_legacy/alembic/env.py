# /backend/migrations/alembic/env.py
# ------------------------------------------------------------
# Alembic 環境設定（FastAPI + SQLAlchemy 2.0 / psycopg3 想定）
# - DSN: POSTGRES_* 環境変数から動的構築（backend_shared.infra.db.url_builder 使用）
# - フォールバック: DB_DSN または DATABASE_URL 環境変数
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
# sys.path に backend_shared と /backend を追加
# このファイルの位置: /backend/migrations/alembic/env.py
# parents[2] = /backend
# ------------------------------------------------------------
BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.append(str(BACKEND_ROOT))

# backend_shared のパスを追加（/opt/backend_shared/src）
BACKEND_SHARED_ROOT = Path("/opt/backend_shared/src")
if BACKEND_SHARED_ROOT.exists() and str(BACKEND_SHARED_ROOT) not in sys.path:
    sys.path.append(str(BACKEND_SHARED_ROOT))

# あなたの SQLAlchemy Base を import
from app.infra.db.orm_models import Base  # noqa: E402

# backend_shared の DB URL 構築ユーティリティを import
try:
    from backend_shared.db.url_builder import build_database_url_with_driver
except ImportError:
    # フォールバック: backend_shared が利用できない場合
    build_database_url_with_driver = None

# Alembic が参照するメタデータ（オートジェネレートの基準）
target_metadata = Base.metadata


def _get_url() -> str:
    """
    データベース接続URLを取得
    
    優先順位:
      1) backend_shared.infra.db.url_builder.build_database_url_with_driver()
         → POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB 環境変数から動的構築
         → Alembic実行時は ALEMBIC_DB_USER で POSTGRES_USER を上書き（DDL権限用）
      2) DB_DSN 環境変数（フォールバック1）
      3) DATABASE_URL 環境変数（フォールバック2）
    
    Returns:
        str: SQLAlchemy用のDSN文字列（postgresql+psycopg://...）
        
    Raises:
        RuntimeError: いずれの方法でもURLを取得できない場合
    """
    # Alembic専用: ALEMBIC_DB_USER が設定されていれば POSTGRES_USER を上書き
    # DDL権限が必要なため、myuser などの管理ユーザーを使用
    alembic_db_user = os.getenv("ALEMBIC_DB_USER")
    if alembic_db_user:
        original_user = os.getenv("POSTGRES_USER")
        os.environ["POSTGRES_USER"] = alembic_db_user
    else:
        original_user = None
    
    try:
        # 方法1: backend_shared の url_builder を使用（推奨）
        if build_database_url_with_driver is not None:
            try:
                url = build_database_url_with_driver(driver="psycopg")
                if url:
                    return url
            except Exception:
                # POSTGRES_* 環境変数が不足している場合はフォールバックへ
                pass
    finally:
        # POSTGRES_USER を元に戻す
        if original_user is not None:
            os.environ["POSTGRES_USER"] = original_user
        elif alembic_db_user:
            os.environ.pop("POSTGRES_USER", None)
    
    # 方法2: DB_DSN 環境変数（フォールバック1）
    url = os.getenv("DB_DSN")
    if url:
        # psycopg3 を明示
        if url.startswith("postgresql://") and "+psycopg" not in url and "+psycopg2" not in url:
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url
    
    # 方法3: DATABASE_URL 環境変数（フォールバック2）
    url = os.getenv("DATABASE_URL")
    if url:
        # psycopg3 を明示
        if url.startswith("postgresql://") and "+psycopg" not in url and "+psycopg2" not in url:
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url
    
    # いずれも取得できない場合はエラー
    raise RuntimeError(
        "Database URL not found. Please set one of:\n"
        "  1) POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB environment variables (recommended)\n"
        "  2) DB_DSN environment variable\n"
        "  3) DATABASE_URL environment variable"
    )


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
