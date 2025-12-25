from __future__ import annotations

from app.core.domain.manuals.manual_entity import ManualDetail, ManualListResponse
from app.core.ports.manuals.manuals_repository import ManualsRepository


class ManualsService:
    def __init__(self, repo: ManualsRepository) -> None:
        self.repo = repo

    def list(
        self,
        *,
        query: str | None,
        tag: str | None,
        category: str | None,
        page: int,
        size: int,
    ) -> ManualListResponse:
        return self.repo.list(query=query, tag=tag, category=category, page=page, size=size)

    def get(self, manual_id: str) -> ManualDetail | None:
        return self.repo.get(manual_id)

    def get_sections(self, manual_id: str):
        return self.repo.get_sections(manual_id)
