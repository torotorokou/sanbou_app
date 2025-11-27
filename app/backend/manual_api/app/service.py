from __future__ import annotations

from typing import Optional
from .repository import InMemoryManualRepository
from .schemas import ManualDetail, ManualListResponse, ManualCatalogResponse


class ManualsService:
    def __init__(self, repo: Optional[InMemoryManualRepository] = None) -> None:
        self.repo = repo or InMemoryManualRepository()

    def list(self, *, query: str | None, tag: str | None, category: str | None, page: int, size: int) -> ManualListResponse:
        return self.repo.list(query=query, tag=tag, category=category, page=page, size=size)

    def get(self, manual_id: str) -> ManualDetail | None:
        return self.repo.get(manual_id)

    def get_sections(self, manual_id: str):
        return self.repo.get_sections(manual_id)

    def get_catalog(self, *, category: str | None = "shogun") -> ManualCatalogResponse:
        return self.repo.get_catalog(category=category)
