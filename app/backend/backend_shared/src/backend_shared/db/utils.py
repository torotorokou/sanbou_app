from __future__ import annotations

from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Executable

async def execute(session: AsyncSession, stmt: Executable) -> Result:
    """シンプルな実行ラッパ。将来リトライ等を入れる場合の拡張ポイント。"""
    return await session.execute(stmt)
