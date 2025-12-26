from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl


class ManualSectionChunk(BaseModel):
    title: str
    anchor: str = Field(..., pattern=r"^s-\d+$")
    html: str | None = None
    markdown: str | None = None


class RagMetadata(BaseModel):
    doc_id: str
    page_title: str
    section_id: str
    url: HttpUrl
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    version: str
    lang: str = "ja"
    breadcrumbs: list[str] = Field(default_factory=list)


class ManualSummary(BaseModel):
    id: str
    title: str
    description: str | None = None
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    version: str | None = None


class ManualDetail(ManualSummary):
    sections: list[ManualSectionChunk] = Field(default_factory=list)
    rag: list[RagMetadata] = Field(default_factory=list)


class ManualListResponse(BaseModel):
    items: list[ManualSummary]
    page: int
    size: int
    total: int


# Catalog for grouped list page (no SQL yet, but future-ready)
class CatalogItem(BaseModel):
    id: str
    title: str
    description: str | None = None
    route: str | None = None
    tags: list[str] = Field(default_factory=list)
    flow_url: str | None = None
    video_url: str | None = None
    thumbnail_url: str | None = None


class CatalogSection(BaseModel):
    id: str
    title: str
    icon: str | None = None  # front maps to Ant icons
    items: list[CatalogItem] = Field(default_factory=list)


class ManualCatalogResponse(BaseModel):
    sections: list[CatalogSection] = Field(default_factory=list)
