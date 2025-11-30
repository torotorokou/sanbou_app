from __future__ import annotations

import os
from typing import Dict, List, Optional

from app.core.domain.manual_entity import (
    ManualDetail,
    ManualListResponse,
    ManualSectionChunk,
    ManualSummary,
    RagMetadata,
    CatalogItem,
    CatalogSection,
    ManualCatalogResponse,
)
from app.core.ports.manuals_repository import ManualsRepository
from app.infra.adapters.catalog_data import sections as CATALOG_SECTIONS


class InMemoryManualRepository(ManualsRepository):
    def __init__(self, base_url: Optional[str] = None) -> None:
        resolved_base_url = base_url or os.getenv("MANUAL_FRONTEND_BASE_URL", "http://localhost:5173")
        self._items: Dict[str, ManualDetail] = {}
        self._seed(resolved_base_url)

    def _seed(self, base_url: str) -> None:
        def build(doc_id: str, title: str, description: str, category: str, tags: List[str]) -> ManualDetail:
            sections: List[ManualSectionChunk] = [
                ManualSectionChunk(title="概要", anchor="s-1", html=f"<h2>概要</h2><p>{description}</p>"),
                ManualSectionChunk(title="手順", anchor="s-2", html="<h2>手順</h2><ol><li>画面を開く</li><li>必要項目を入力</li><li>保存</li></ol>"),
                ManualSectionChunk(title="注意点", anchor="s-3", html="<h2>注意点</h2><ul><li>権限を確認</li><li>入力値を再確認</li></ul>"),
            ]
            rag: List[RagMetadata] = [
                RagMetadata(
                    doc_id=f"manual-{doc_id}",
                    page_title=title,
                    section_id=s.anchor,
                    url=f"{base_url}/manuals/shogun/{doc_id}#{s.anchor}",  # type: ignore
                    category=category,
                    tags=tags,
                    version="2025-09-18",
                    lang="ja",
                    breadcrumbs=["マニュアル", "将軍", title],
                )
                for s in sections
            ]
            return ManualDetail(
                id=doc_id,
                title=title,
                description=description,
                category=category,
                tags=tags,
                version="2025-09-18",
                sections=sections,
                rag=rag,
            )

        item1 = build("estimate-make", "見積書の作成フロー", "見積作成の全体像", "shogun", ["見積", "営業"])
        item2 = build("mf-honest-out", "工場外のオネスト運搬のマニフェスト入力", "工場外マニフェスト入力の流れ", "shogun", ["マニフェスト", "E票"])
        self._items[item1.id] = item1
        self._items[item2.id] = item2

    def list(self, *, query: Optional[str] = None, tag: Optional[str] = None, category: Optional[str] = None, page: int = 1, size: int = 20) -> ManualListResponse:
        items = list(self._items.values())
        if category:
            items = [x for x in items if x.category == category]
        if tag:
            items = [x for x in items if tag in (x.tags or [])]
        if query:
            q = query.lower()
            items = [x for x in items if q in x.title.lower() or (x.description or "").lower().find(q) >= 0 or any(q in t.lower() for t in (x.tags or []))]
        total = len(items)
        start = max((page - 1) * size, 0)
        end = start + size
        summaries: List[ManualSummary] = [
            ManualSummary(id=x.id, title=x.title, description=x.description, category=x.category, tags=x.tags, version=x.version)
            for x in items[start:end]
        ]
        return ManualListResponse(items=summaries, page=page, size=size, total=total)

    def get(self, manual_id: str) -> Optional[ManualDetail]:
        return self._items.get(manual_id)

    def get_sections(self, manual_id: str) -> List[ManualSectionChunk]:
        m = self._items.get(manual_id)
        return m.sections if m else []

    def get_catalog(self, *, category: Optional[str] = "shogun") -> ManualCatalogResponse:
        # Load from static dataset (migrated from frontend). Future: replace with SQL-backed repository.
        sections: List[CatalogSection] = []
        for sec in CATALOG_SECTIONS:
            items = [
                CatalogItem(
                    id=str(it.get("id", "")),
                    title=str(it.get("title", "")),
                    description=it.get("description"),
                    route=it.get("route"),
                    tags=it.get("tags", []),
                    flow_url=it.get("flow_url"),
                    video_url=it.get("video_url"),
                    thumbnail_url=it.get("thumbnail_url"),
                )
                for it in sec.get("items", [])
            ]
            sections.append(
                CatalogSection(
                    id=str(sec.get("id", "")),
                    title=str(sec.get("title", "")),
                    icon=sec.get("icon"),
                    items=items,
                )
            )
        return ManualCatalogResponse(sections=sections)
