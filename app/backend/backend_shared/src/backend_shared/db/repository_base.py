from __future__ import annotations

from typing import Generic, Optional, Protocol, Sequence, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")

class AsyncRepository(Protocol, Generic[T]):
    """各サービス側で具象化するための最小 I/F。"""
    async def get(self, session: AsyncSession, id: int) -> Optional[T]: ...
    async def add(self, session: AsyncSession, obj: T) -> T: ...
    async def list(self, session: AsyncSession, limit: int = 100) -> Sequence[T]: ...

class SQLAlchemyAsyncRepository(Generic[T]):
    """
    汎用的な SQLAlchemy 実装(model クラスを渡して使う)。
    ドメイン固有のクエリは各サービスで拡張してください。
    """
    def __init__(self, model: type[T]) -> None:
        self.model = model

    async def get(self, session: AsyncSession, id: int) -> Optional[T]:
        return await session.get(self.model, id)

    async def add(self, session: AsyncSession, obj: T) -> T:
        session.add(obj)
        # PK 採番などのために flush(commit は上位の session_scope が実施)
        await session.flush()
        return obj

    async def list(self, session: AsyncSession, limit: int = 100) -> Sequence[T]:
        res = await session.execute(select(self.model).limit(limit))
        return list(res.scalars().all())
