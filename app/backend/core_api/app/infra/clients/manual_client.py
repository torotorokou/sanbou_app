"""
Manual API Client - マニュアル/ドキュメントサービス内部HTTPクライアント

マニュアルサービスと通信し、マニュアル一覧取得、
特定マニュアルの詳細情報取得を実現。

機能:
  - 利用可能なマニュアル一覧の取得
  - 特定マニュアルIDで詳細情報取得
  - マニュアルのメタデータ(タイトル、カテゴリ等)取得

タイムアウト設定:
  - connect: 1.0s
  - read: 5.0s
  - write: 5.0s
  - pool: 1.0s

使用例:
    client = ManualClient()
    manuals = await client.list_manuals()
    for manual in manuals:
        print(f"{manual['id']}: {manual['title']}")
"""

import os

import httpx
from backend_shared.application.logging import get_module_logger

logger = get_module_logger(__name__)

MANUAL_API_BASE = os.getenv("MANUAL_API_BASE", "http://manual_api:8000")
TIMEOUT = httpx.Timeout(connect=1.0, read=5.0, write=5.0, pool=1.0)


class ManualClient:
    """Client for Manual API internal HTTP calls."""

    def __init__(self, base_url: str = MANUAL_API_BASE):
        self.base_url = base_url.rstrip("/")

    async def list_manuals(self) -> list[dict]:
        """
        List all available manuals.

        Returns:
            List of manual metadata dicts

        Raises:
            httpx.TimeoutException: If request times out
            httpx.HTTPStatusError: If Manual API returns error status
        """
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            logger.info(f"Calling Manual API: {self.base_url}/list")
            response = await client.get(f"{self.base_url}/list")
            response.raise_for_status()
            data = response.json()
            manuals = data.get("manuals", [])
            logger.info("Manual API response received", extra={"count": len(manuals)})
            return manuals

    async def get_manual(self, manual_id: str) -> dict:
        """Get specific manual by ID."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            logger.info(f"Calling Manual API: {self.base_url}/manuals/{manual_id}")
            response = await client.get(f"{self.base_url}/manuals/{manual_id}")
            response.raise_for_status()
            return response.json()
