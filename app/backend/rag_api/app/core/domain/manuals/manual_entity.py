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
    tags: list[str] = []
    version: str
    lang: str = "ja"
    breadcrumbs: list[str] = []


class ManualSummary(BaseModel):
    id: str
    title: str
    description: str | None = None
    category: str | None = None
    tags: list[str] = []
    version: str | None = None


class ManualDetail(ManualSummary):
    sections: list[ManualSectionChunk] = []
    rag: list[RagMetadata] = []


class ManualListResponse(BaseModel):
    items: list[ManualSummary]
    page: int
    size: int
    total: int
