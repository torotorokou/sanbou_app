from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class ManualSectionChunk(BaseModel):
    title: str
    anchor: str = Field(..., pattern=r"^s-\d+$")
    html: Optional[str] = None
    markdown: Optional[str] = None


class RagMetadata(BaseModel):
    doc_id: str
    page_title: str
    section_id: str
    url: HttpUrl
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    version: str
    lang: str = "ja"
    breadcrumbs: List[str] = Field(default_factory=list)


class ManualSummary(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    version: Optional[str] = None


class ManualDetail(ManualSummary):
    sections: List[ManualSectionChunk] = Field(default_factory=list)
    rag: List[RagMetadata] = Field(default_factory=list)


class ManualListResponse(BaseModel):
    items: List[ManualSummary]
    page: int
    size: int
    total: int


# Catalog for grouped list page (no SQL yet, but future-ready)
class CatalogItem(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    route: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    flow_url: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None


class CatalogSection(BaseModel):
    id: str
    title: str
    icon: Optional[str] = None  # front maps to Ant icons
    items: List[CatalogItem] = Field(default_factory=list)


class ManualCatalogResponse(BaseModel):
    sections: List[CatalogSection] = Field(default_factory=list)
