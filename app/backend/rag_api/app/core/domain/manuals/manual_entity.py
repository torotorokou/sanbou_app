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
    tags: List[str] = []
    version: str
    lang: str = "ja"
    breadcrumbs: List[str] = []


class ManualSummary(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = []
    version: Optional[str] = None


class ManualDetail(ManualSummary):
    sections: List[ManualSectionChunk] = []
    rag: List[RagMetadata] = []


class ManualListResponse(BaseModel):
    items: List[ManualSummary]
    page: int
    size: int
    total: int
