"""
Catalog Data for Manual API
カタログデータ（セクション別マニュアル一覧）

**Single Source of Truth**: local_data/manuals/index.json

このファイルは index.json をカタログ正本として読み込み、
major フィールドでセクションを自動グループ化します。

将来の移行ポイント:
- load_manual_index() で GCS から取得するよう変更
- build_manual_asset_url() で GCS 署名付き URL を生成
- load_manual_content() で GCS 上の Markdown を取得
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional, TypedDict

from backend_shared.application.logging import get_module_logger


logger = get_module_logger(__name__)


# =============================================================================
# Type Definitions
# =============================================================================


class ManualAssets(TypedDict, total=False):
    """マニュアルアセット（サムネイル、動画、フローチャート）"""

    thumb: Optional[str]
    video: Optional[str]
    flowchart: Optional[str]


class ManualItem(TypedDict):
    """index.json のマニュアル項目"""

    id: str
    no: int
    major: str
    title: str
    description: str
    order: int
    icon: str
    tags: list[str]
    assets: ManualAssets
    content_path: str


class ManualIndex(TypedDict):
    """index.json のルート構造"""

    version: int
    manuals: list[ManualItem]


class CatalogItem(TypedDict, total=False):
    """カタログ形式のアイテム（API レスポンス用）"""

    id: str
    title: str
    description: Optional[str]
    tags: list[str]
    route: str
    thumbnail_url: Optional[str]
    video_url: Optional[str]
    flow_url: Optional[str]


class CatalogSection(TypedDict):
    """カタログセクション（major でグループ化）"""

    id: str
    title: str
    icon: str
    items: list[CatalogItem]


# =============================================================================
# URL Builders
# =============================================================================


def _get_asset_base_url() -> str:
    """マニュアルアセットのベースURLを取得

    環境変数 MANUAL_ASSET_BASE_URL があればそれを使用
    なければ /core_api/manual/manual-assets を使用（BFF経由）
    """
    env_url = os.getenv("MANUAL_ASSET_BASE_URL", "").strip()
    if env_url:
        return env_url.rstrip("/")
    return "/core_api/manual/manual-assets"


def build_manual_asset_url(relative_path: Optional[str]) -> Optional[str]:
    """マニュアルアセットのURLを生成

    Args:
        relative_path: 相対パス（例: thumbs/m11_master_vendor.png）

    Returns:
        完全なURL or None
    """
    if not relative_path:
        return None
    if relative_path.startswith(("http://", "https://")):
        return relative_path
    base = _get_asset_base_url()
    return f"{base}/{relative_path.lstrip('/')}"


# 後方互換性エイリアス
build_manual_video_asset_url = build_manual_asset_url


# =============================================================================
# Index Loader
# =============================================================================


def _get_index_path() -> Path:
    """index.json のパスを取得"""
    return (
        Path(__file__).resolve().parent.parent.parent.parent
        / "local_data"
        / "manuals"
        / "index.json"
    )


def _get_contents_dir() -> Path:
    """contents/ ディレクトリのパスを取得"""
    return _get_index_path().parent / "contents"


@lru_cache(maxsize=1)
def load_manual_index() -> ManualIndex:
    """index.json を読み込む（Single Source of Truth）"""
    index_path = _get_index_path()
    if not index_path.exists():
        logger.warning(f"Manual index not found: {index_path}")
        return {"version": 0, "manuals": []}

    try:
        with open(index_path, encoding="utf-8") as f:
            data: ManualIndex = json.load(f)
        logger.info(
            f"Loaded {len(data.get('manuals', []))} manuals from index (v{data.get('version', 0)})"
        )
        return data
    except Exception as e:
        logger.error(f"Failed to load manual index: {e}")
        return {"version": 0, "manuals": []}


# 後方互換性エイリアス
def load_video_index() -> list[dict]:
    """後方互換: 旧形式で manuals を返す"""
    index = load_manual_index()
    return index.get("manuals", [])


# =============================================================================
# Content Loader
# =============================================================================


def load_manual_content(content_path: str) -> Optional[str]:
    """マニュアルのMarkdownコンテンツを読み込む

    Args:
        content_path: 相対パス（例: contents/m11_master_vendor.md）

    Returns:
        Markdown 文字列 or None
    """
    if not content_path:
        return None

    full_path = _get_index_path().parent / content_path
    if not full_path.exists():
        logger.warning(f"Manual content not found: {full_path}")
        return None

    try:
        with open(full_path, encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to load manual content: {e}")
        return None


# =============================================================================
# Catalog Builders (新スキーマ対応)
# =============================================================================


def _manual_to_catalog_item(manual: ManualItem) -> CatalogItem:
    """ManualItem を CatalogItem に変換"""
    assets = manual.get("assets", {})
    return {
        "id": manual["id"],
        "title": manual["title"],
        "description": manual.get("description"),
        "tags": manual.get("tags", []),
        "route": f"/manuals/shogun/{manual['id']}",
        "thumbnail_url": build_manual_asset_url(assets.get("thumb")),
        "video_url": build_manual_asset_url(assets.get("video")),
        "flow_url": build_manual_asset_url(assets.get("flowchart")),
    }


def get_catalog_sections() -> list[CatalogSection]:
    """index.json から major 別セクションを生成

    Returns:
        CatalogSection のリスト（order 順）
    """
    index = load_manual_index()
    manuals = index.get("manuals", [])

    if not manuals:
        return []

    # major 別にグループ化
    major_groups: dict[str, list[ManualItem]] = {}
    for manual in manuals:
        major = manual.get("major", "その他")
        if major not in major_groups:
            major_groups[major] = []
        major_groups[major].append(manual)

    # セクションを生成（order 順）
    result: list[CatalogSection] = []
    for major, items in major_groups.items():
        # items を order でソート
        sorted_items = sorted(items, key=lambda x: x.get("order", 999))
        # 最初のアイテムの icon を使用
        icon = sorted_items[0].get("icon", "FileOutlined") if sorted_items else "FileOutlined"
        # ID は major の最初の2桁から生成
        section_id = f"sec-{sorted_items[0]['no'] // 10}" if sorted_items else major

        result.append(
            {
                "id": section_id,
                "title": major,
                "icon": icon,
                "items": [_manual_to_catalog_item(m) for m in sorted_items],
            }
        )

    # セクションを最初のアイテムの order でソート
    result.sort(key=lambda s: s["items"][0]["id"] if s["items"] else "zzz")
    return result


def get_manual_by_id(manual_id: str) -> Optional[ManualItem]:
    """ID でマニュアルを取得"""
    index = load_manual_index()
    for manual in index.get("manuals", []):
        if manual["id"] == manual_id:
            return manual
    return None


def get_manual_detail(manual_id: str) -> Optional[dict]:
    """マニュアル詳細（content 含む）を取得"""
    manual = get_manual_by_id(manual_id)
    if not manual:
        return None

    assets = manual.get("assets", {})
    content = load_manual_content(manual.get("content_path", ""))

    return {
        **manual,
        "content": content,
        "thumbnail_url": build_manual_asset_url(assets.get("thumb")),
        "video_url": build_manual_asset_url(assets.get("video")),
        "flowchart_url": build_manual_asset_url(assets.get("flowchart")),
    }


# =============================================================================
# 後方互換用エイリアス（既存コードからの移行用）
# =============================================================================


def get_video_sections() -> list[dict]:
    """後方互換: get_catalog_sections のエイリアス"""
    return get_catalog_sections()


# 旧 sections 変数の代替 (動的生成)
# 使用箇所: manuals_repository.py の CATALOG_SECTIONS
sections = property(lambda self: get_catalog_sections())


def get_sections() -> list[CatalogSection]:
    """sections 変数の代替関数"""
    return get_catalog_sections()
