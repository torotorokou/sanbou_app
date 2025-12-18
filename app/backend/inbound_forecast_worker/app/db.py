"""
Database Connection for Inbound Forecast Worker
================================================
Purpose: Worker専用のDB接続管理

Worker特性:
- 長時間稼働するプロセス
- 定期的なDB接続（5秒ごと）
- 接続プールの適切な管理が必要

Note:
    backend_shared.db.session.SyncDatabaseSessionManager を使用する統一実装に移行しました。
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy.orm import Session

from backend_shared.application.logging import get_module_logger
from backend_shared.db import build_database_url_with_driver, SyncDatabaseSessionManager

logger = get_module_logger(__name__)


# ==========================================
# Database URL 構築
# ==========================================
def get_database_url() -> str:
    """
    環境変数からDATABASE_URLを取得
    
    優先順位:
    1. backend_shared.db.build_database_url_with_driver()
       → POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB 環境変数から動的構築
    2. DATABASE_URL 環境変数（フォールバック）
    
    Returns:
        str: PostgreSQL接続URL
    
    Raises:
        ValueError: DATABASE_URLが設定されていない場合
    """
    # 方法1: backend_shared の url_builder を使用（推奨）
    try:
        db_url = build_database_url_with_driver(driver="psycopg")
        logger.debug("Database URL built from POSTGRES_* env vars")
        return db_url
    except Exception as e:
        logger.debug(f"Failed to build URL from POSTGRES_* env vars: {e}")
    
    # 方法2: DATABASE_URL 環境変数（フォールバック）
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        logger.debug("Database URL from DATABASE_URL env var")
        return db_url
    
    raise ValueError(
        "Cannot build database URL. "
        "Set POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB or DATABASE_URL"
    )


# ==========================================
# Session Manager（統一実装）
# ==========================================
_db_manager: SyncDatabaseSessionManager | None = None


def get_db_manager() -> SyncDatabaseSessionManager:
    """
    SyncDatabaseSessionManager を取得（シングルトン）
    
    Worker用の最適化設定:
    - pool_size: 5 (最大同時接続数)
    - max_overflow: 0 (pool_sizeを超える一時接続を許可しない)
    - pool_pre_ping: True (接続前に生存確認)
    - pool_recycle: 3600 (1時間でコネクションを再作成)
    
    Returns:
        SyncDatabaseSessionManager: セッションマネージャー
    """
    global _db_manager
    if _db_manager is None:
        db_url = get_database_url()
        _db_manager = SyncDatabaseSessionManager(
            db_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=0,
            pool_recycle=3600,
        )
        logger.info("✅ Database manager initialized", extra={"db_url": db_url.split("@")[-1]})
    return _db_manager


# ==========================================
# Session Context Manager
# ==========================================
@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    DB Session のコンテキストマネージャ
    
    Usage:
        with get_db_session() as db:
            result = db.execute(...)
    
    Yields:
        Session: SQLAlchemy Session
        
    Note:
        backend_shared.db.session.SyncDatabaseSessionManager.session_scope() を使用します。
    """
    db_manager = get_db_manager()
    with db_manager.session_scope() as session:
        yield session
