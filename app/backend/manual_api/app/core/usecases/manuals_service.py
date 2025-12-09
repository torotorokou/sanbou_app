from __future__ import annotations

from typing import Optional

from backend_shared.application.logging import get_module_logger
from app.core.ports.manuals_repository import ManualsRepository
from app.core.domain.manual_entity import ManualDetail, ManualListResponse, ManualCatalogResponse

logger = get_module_logger(__name__)


class ManualsService:
    def __init__(self, repo: ManualsRepository) -> None:
        self.repo = repo

    def list(self, *, query: str | None, tag: str | None, category: str | None, page: int, size: int) -> ManualListResponse:
        logger.info("List manuals", extra={"query": query, "tag": tag, "category": category, "page": page, "size": size})
        return self.repo.list(query=query, tag=tag, category=category, page=page, size=size)

    def get(self, manual_id: str) -> ManualDetail | None:
        logger.info("Get manual", extra={"manual_id": manual_id})
        return self.repo.get(manual_id)

    def get_sections(self, manual_id: str):
        logger.info("Get manual sections", extra={"manual_id": manual_id})
        return self.repo.get_sections(manual_id)

    def get_catalog(self, *, category: str | None = "shogun") -> ManualCatalogResponse:
        logger.info("Get manual catalog", extra={"category": category})
        return self.repo.get_catalog(category=category)
