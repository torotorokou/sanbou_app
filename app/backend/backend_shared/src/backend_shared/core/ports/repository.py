"""
Repository Port

データ永続化層の抽象インターフェース。
"""

from typing import Generic, Optional, Protocol, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class AsyncRepository(Protocol, Generic[T]):
    """非同期 Repository の抽象インターフェース"""

    async def get_by_id(self, id: int) -> Optional[T]:
        """ID でエンティティを取得"""
        ...

    async def list_all(self) -> list[T]:
        """全エンティティを取得"""
        ...

    async def add(self, entity: T) -> T:
        """エンティティを追加"""
        ...

    async def update(self, entity: T) -> T:
        """エンティティを更新"""
        ...

    async def delete(self, id: int) -> None:
        """エンティティを削除"""
        ...
