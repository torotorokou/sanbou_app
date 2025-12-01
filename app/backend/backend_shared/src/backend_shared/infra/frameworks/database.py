from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

class DatabaseSessionManager:
    """
    非同期 SQLAlchemy 用の共通セッション管理。
    - session_scope(): commit/rollback を自動制御
    - get_session(): FastAPI Depends 用のラッパ
    """
    def __init__(self, db_url: str, *, echo: bool = False, pool_pre_ping: bool = True) -> None:
        self.db_url = db_url
        self.engine = create_async_engine(
            db_url, echo=echo, pool_pre_ping=pool_pre_ping, future=True
        )
        self._session_factory = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        return self._session_factory

    @asynccontextmanager
    async def session_scope(self) -> AsyncGenerator[AsyncSession, None]:
        """トランザクション境界。正常なら commit、例外時は rollback。"""
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    # FastAPI の Depends にそのまま渡せる形
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.session_scope() as session:
            yield session

    async def dispose(self) -> None:
        """接続プールを明示的に破棄(アプリ終了時など)。"""
        await self.engine.dispose()
