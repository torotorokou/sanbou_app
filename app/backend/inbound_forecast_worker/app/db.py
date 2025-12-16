"""
Database Connection for Inbound Forecast Worker
================================================
Purpose: Worker専用のDB接続管理

Worker特性:
- 長時間稼働するプロセス
- 定期的なDB接続（5秒ごと）
- 接続プールの適切な管理が必要
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from backend_shared.application.logging import get_module_logger

logger = get_module_logger(__name__)


# ==========================================
# Database URL 構築
# ==========================================
def get_database_url() -> str:
    """
    環境変数からDATABASE_URLを取得
    
    優先順位:
    1. backend_shared.infra.db.url_builder.build_database_url_with_driver()
       → POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB 環境変数から動的構築
    2. DATABASE_URL 環境変数（フォールバック）
    
    Returns:
        str: PostgreSQL接続URL
    
    Raises:
        ValueError: DATABASE_URLが設定されていない場合
    """
    # 方法1: backend_shared の url_builder を使用（推奨）
    try:
        from backend_shared.infra.db.url_builder import build_database_url_with_driver
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
# Engine 初期化（シングルトン）
# ==========================================
_engine = None


def get_engine():
    """
    SQLAlchemy Engine を取得（シングルトン）
    
    Pool設定:
    - pool_size: 5 (最大同時接続数)
    - max_overflow: 0 (pool_sizeを超える一時接続を許可しない)
    - pool_pre_ping: True (接続前に生存確認)
    - pool_recycle: 3600 (1時間でコネクションを再作成)
    
    Returns:
        Engine: SQLAlchemy Engine
    """
    global _engine
    if _engine is None:
        db_url = get_database_url()
        _engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=0,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False,
        )
        logger.info("✅ Database engine initialized", extra={"db_url": db_url.split("@")[-1]})
    return _engine


# ==========================================
# Session Factory
# ==========================================
def get_session_factory() -> sessionmaker:
    """
    Session Factory を取得
    
    Returns:
        sessionmaker: SQLAlchemy Session Factory
    """
    engine = get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
    """
    SessionFactory = get_session_factory()
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()
