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
from logging.config import fileConfig
from pathlib import Path

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
    from backend_shared.infra.db.url_builder import build_database_url_with_driver
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
         → DB_MIGRATOR_USER / DB_MIGRATOR_PASSWORD 環境変数を優先
         → 未設定の場合は DB_USER / DB_PASSWORD にフォールバック
         → さらに未設定の場合は POSTGRES_* にフォールバック
      2) DB_DSN 環境変数（フォールバック1）
      3) DATABASE_URL 環境変数（フォールバック2）

    Returns:
        str: SQLAlchemy用のDSN文字列（postgresql+psycopg://...）

    Raises:
        RuntimeError: いずれの方法でもURLを取得できない場合

    Notes:
        - 旧仕様の ALEMBIC_DB_USER は非推奨（後方互換性のため一時的にサポート）
        - 新仕様では DB_MIGRATOR_USER を使用
        - DB_MIGRATOR_USER が未設定の場合は自動的に DB_USER にフォールバック
    """
    # 後方互換性: ALEMBIC_DB_USER が設定されている場合は警告してフォールバック
    # 新しい実装では DB_MIGRATOR_USER を使用
    alembic_db_user = os.getenv("ALEMBIC_DB_USER")
    if alembic_db_user:
        import warnings

        warnings.warn(
            "ALEMBIC_DB_USER is deprecated. Please use DB_MIGRATOR_USER instead. "
            "ALEMBIC_DB_USER will be removed in a future version.",
            DeprecationWarning,
            stacklevel=2,
        )
        # 一時的に DB_MIGRATOR_USER にマッピング
        if not os.getenv("DB_MIGRATOR_USER"):
            os.environ["DB_MIGRATOR_USER"] = alembic_db_user

    try:
        # 方法1: backend_shared の url_builder を使用（推奨）
        # mode="migrator" により、DB_MIGRATOR_USER を優先、未設定時は DB_USER にフォールバック
        if build_database_url_with_driver is not None:
            try:
                url = build_database_url_with_driver(driver="psycopg")
                # build_database_url に mode パラメータを追加する必要がある
                # 現在は後方互換性のため、従来通り env から取得
                # 将来的には: url = build_database_url(driver="psycopg", mode="migrator")
                if url:
                    return url
            except Exception:
                # DB_* 環境変数が不足している場合はフォールバックへ
                pass
    finally:
        pass

    # 方法2: DB_DSN 環境変数（フォールバック1）
    url = os.getenv("DB_DSN")
    if url:
        # psycopg3 を明示
        if (
            url.startswith("postgresql://")
            and "+psycopg" not in url
            and "+psycopg2" not in url
        ):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url

    # 方法3: DATABASE_URL 環境変数（フォールバック2）
    url = os.getenv("DATABASE_URL")
    if url:
        # psycopg3 を明示
        if (
            url.startswith("postgresql://")
            and "+psycopg" not in url
            and "+psycopg2" not in url
        ):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url

    # いずれも取得できない場合はエラー
    raise RuntimeError(
        "Database URL not found. Please set one of:\n"
        "  1) DB_USER, DB_PASSWORD, DB_NAME (or DB_MIGRATOR_* for migrations)\n"
        "  2) POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB (legacy)\n"
        "  3) DB_DSN environment variable\n"
        "  4) DATABASE_URL environment variable\n"
        "\n"
        "For migration-specific users (with DDL permissions), set:\n"
        "  - DB_MIGRATOR_USER\n"
        "  - DB_MIGRATOR_PASSWORD\n"
        "If not set, will fall back to DB_USER / DB_PASSWORD."
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
        include_schemas=True,  # 複数スキーマの差分を含める
        compare_type=True,  # 型の差分検出
        compare_server_default=True,  # サーバデフォルトの差分検出
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
        include_schemas=True,  # 複数スキーマの差分を含める
        compare_type=True,  # 型の差分検出
        compare_server_default=True,  # サーバデフォルトの差分検出
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
