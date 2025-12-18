"""
Database Session Management

Provides unified session management for both sync and async SQLAlchemy operations.

Features:
- Async session manager (FastAPI, async workers)
- Sync session manager (sync workers, scripts)
- Connection pooling optimization
- Automatic transaction management
- Dependency injection support

Usage:
    # Async (FastAPI)
    from backend_shared.db.session import DatabaseSessionManager
    
    db_manager = DatabaseSessionManager(db_url)
    
    @app.get("/")
    async def endpoint(session: AsyncSession = Depends(db_manager.get_session)):
        result = await session.execute(...)
    
    # Sync (Worker)
    from backend_shared.db.session import SyncDatabaseSessionManager
    
    db_manager = SyncDatabaseSessionManager(db_url)
    
    with db_manager.session_scope() as session:
        result = session.execute(...)
"""
from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine, Engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker, AsyncEngine
from sqlalchemy.orm import Session, sessionmaker


class DatabaseSessionManager:
    """
    非同期 SQLAlchemy 用の共通セッション管理
    
    FastAPI などの非同期フレームワークで使用します。
    
    Features:
    - Automatic transaction management (commit/rollback)
    - Connection pooling
    - Dependency injection support
    
    Example:
        db_manager = DatabaseSessionManager(db_url)
        
        @app.get("/")
        async def endpoint(session: AsyncSession = Depends(db_manager.get_session)):
            result = await session.execute(...)
    """
    
    def __init__(
        self,
        db_url: str,
        *,
        echo: bool = False,
        pool_pre_ping: bool = True,
        pool_size: int = 5,
        max_overflow: int = 10,
    ) -> None:
        """
        コンストラクタ
        
        Args:
            db_url: データベース接続URL (postgresql+asyncpg://...)
            echo: SQL ログ出力を有効化するか
            pool_pre_ping: 接続プールの事前 ping を有効化するか
            pool_size: コネクションプールのサイズ
            max_overflow: pool_size を超えて許可する追加接続数
        """
        self.db_url = db_url
        self.engine = create_async_engine(
            db_url,
            echo=echo,
            pool_pre_ping=pool_pre_ping,
            pool_size=pool_size,
            max_overflow=max_overflow,
            future=True,
        )
        self._session_factory = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """セッションファクトリーを取得"""
        return self._session_factory

    @asynccontextmanager
    async def session_scope(self) -> AsyncGenerator[AsyncSession, None]:
        """
        トランザクション境界を持つセッションを提供
        
        正常終了時は自動的にcommit、例外発生時は自動的にrollbackします。
        
        Example:
            async with db_manager.session_scope() as session:
                result = await session.execute(...)
                # 正常終了時は自動commit、例外時は自動rollback
        """
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        FastAPI Depends 用のセッション生成関数
        
        Example:
            @app.get("/")
            async def endpoint(session: AsyncSession = Depends(db_manager.get_session)):
                result = await session.execute(...)
        """
        async with self.session_scope() as session:
            yield session

    async def dispose(self) -> None:
        """接続プールを明示的に破棄（アプリ終了時など）"""
        await self.engine.dispose()


class SyncDatabaseSessionManager:
    """
    同期 SQLAlchemy 用の共通セッション管理
    
    Worker や CLI スクリプトなど、同期処理で使用します。
    
    Features:
    - Automatic transaction management (commit/rollback)
    - Connection pooling with appropriate settings for long-running processes
    - Context manager support
    
    Example:
        db_manager = SyncDatabaseSessionManager(db_url)
        
        with db_manager.session_scope() as session:
            result = session.execute(...)
    """
    
    def __init__(
        self,
        db_url: str,
        *,
        echo: bool = False,
        pool_pre_ping: bool = True,
        pool_size: int = 5,
        max_overflow: int = 0,
        pool_recycle: int = 3600,
    ) -> None:
        """
        コンストラクタ
        
        Args:
            db_url: データベース接続URL (postgresql+psycopg://...)
            echo: SQL ログ出力を有効化するか
            pool_pre_ping: 接続プールの事前 ping を有効化するか
            pool_size: コネクションプールのサイズ
            max_overflow: pool_size を超えて許可する追加接続数（Worker では0推奨）
            pool_recycle: コネクションの自動リサイクル時間（秒）
        """
        self.db_url = db_url
        self.engine = create_engine(
            db_url,
            echo=echo,
            pool_pre_ping=pool_pre_ping,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_recycle=pool_recycle,
            future=True,
        )
        self._session_factory = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    @property
    def session_factory(self) -> sessionmaker:
        """セッションファクトリーを取得"""
        return self._session_factory

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        トランザクション境界を持つセッションを提供
        
        正常終了時は自動的にcommit、例外発生時は自動的にrollbackします。
        
        Example:
            with db_manager.session_scope() as session:
                result = session.execute(...)
                # 正常終了時は自動commit、例外時は自動rollback
        """
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_session(self) -> Generator[Session, None, None]:
        """
        依存性注入用のセッション生成関数
        
        Example:
            def my_function(session: Session = Depends(db_manager.get_session)):
                result = session.execute(...)
        """
        with self.session_scope() as session:
            yield session

    def dispose(self) -> None:
        """接続プールを明示的に破棄（アプリ終了時など）"""
        self.engine.dispose()
