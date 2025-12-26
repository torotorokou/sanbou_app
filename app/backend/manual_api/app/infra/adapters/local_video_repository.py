"""
Local Manual Video Repository
index.json からマニュアル動画メタデータを読み込むリポジトリ実装

将来GCSに移行する際は、このファイルを GcsManualVideoRepository に差し替える
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from backend_shared.application.logging import get_module_logger


if TYPE_CHECKING:
    pass

logger = get_module_logger(__name__)


# =============================================================================
# Schema / DTOs
# =============================================================================


class ManualVideoItem(BaseModel):
    """マニュアル動画アイテム（index.json の1レコードに対応）"""

    id: str
    title: str
    description: str | None = None
    category: str | None = None
    order: int = 0
    tags: list[str] = Field(default_factory=list)
    thumb_path: str | None = None
    video_path: str | None = None


class ManualVideoIndex(BaseModel):
    """マニュアル動画一覧（index.json 全体）"""

    items: list[ManualVideoItem] = Field(default_factory=list)


# =============================================================================
# Repository Interface (Port)
# =============================================================================


class ManualVideoRepository:
    """マニュアル動画リポジトリの抽象インターフェース

    将来 GCS 実装に差し替える場合はこのインターフェースを実装する
    """

    def list_all(self) -> list[ManualVideoItem]:
        """全アイテムを取得"""
        raise NotImplementedError

    def get(self, item_id: str) -> ManualVideoItem | None:
        """ID でアイテムを取得"""
        raise NotImplementedError

    def list_by_category(self, category: str) -> list[ManualVideoItem]:
        """カテゴリでフィルタ"""
        raise NotImplementedError

    def build_thumb_url(self, item: ManualVideoItem) -> str | None:
        """サムネイルURLを生成"""
        raise NotImplementedError

    def build_video_url(self, item: ManualVideoItem) -> str | None:
        """動画URLを生成"""
        raise NotImplementedError


# =============================================================================
# Local Implementation (Infra/Adapter)
# =============================================================================


class LocalManualVideoRepository(ManualVideoRepository):
    """ローカルファイルシステムからマニュアル動画を読み込むリポジトリ

    - index.json からメタデータを読み込み
    - アセットURLは MANUAL_ASSET_BASE_URL または /manual-assets を使用
    """

    def __init__(
        self,
        index_path: Path | None = None,
        asset_base_url: str | None = None,
    ) -> None:
        # デフォルトパス: local_data/manuals/index.json
        if index_path is None:
            index_path = (
                Path(__file__).resolve().parent.parent.parent.parent
                / "local_data"
                / "manuals"
                / "index.json"
            )

        self._index_path = index_path
        self._asset_base_url = asset_base_url or self._get_default_asset_base_url()
        self._items: dict[str, ManualVideoItem] = {}
        self._load()

    @staticmethod
    def _get_default_asset_base_url() -> str:
        """デフォルトのアセットベースURLを取得

        環境変数 MANUAL_ASSET_BASE_URL があればそれを使用
        なければ /core_api/manual/manual-assets を使用（BFF経由）
        """
        import os

        env_url = os.getenv("MANUAL_ASSET_BASE_URL", "").strip()
        if env_url:
            return env_url.rstrip("/")
        return "/core_api/manual/manual-assets"

    def _load(self) -> None:
        """index.json を読み込んでキャッシュ"""
        if not self._index_path.exists():
            logger.warning(
                f"Manual video index not found: {self._index_path}",
                extra={"operation": "load_index", "path": str(self._index_path)},
            )
            return

        try:
            with open(self._index_path, encoding="utf-8") as f:
                data = json.load(f)

            items = [ManualVideoItem(**item) for item in data]
            self._items = {item.id: item for item in items}

            logger.info(
                f"Loaded {len(self._items)} manual video items from index.json",
                extra={"operation": "load_index", "count": len(self._items)},
            )
        except Exception as e:
            logger.error(
                f"Failed to load manual video index: {e}",
                extra={"operation": "load_index", "error": str(e)},
            )

    def list_all(self) -> list[ManualVideoItem]:
        """全アイテムを取得（order順）"""
        items = list(self._items.values())
        items.sort(key=lambda x: (x.category or "", x.order))
        return items

    def get(self, item_id: str) -> ManualVideoItem | None:
        """ID でアイテムを取得"""
        return self._items.get(item_id)

    def list_by_category(self, category: str) -> list[ManualVideoItem]:
        """カテゴリでフィルタ"""
        items = [item for item in self._items.values() if item.category == category]
        items.sort(key=lambda x: x.order)
        return items

    def build_thumb_url(self, item: ManualVideoItem) -> str | None:
        """サムネイルURLを生成"""
        if not item.thumb_path:
            return None
        return f"{self._asset_base_url}/{item.thumb_path}"

    def build_video_url(self, item: ManualVideoItem) -> str | None:
        """動画URLを生成"""
        if not item.video_path:
            return None
        return f"{self._asset_base_url}/{item.video_path}"
