import builtins
from abc import ABC, abstractmethod

from app.core.domain.manual_entity import (
    ManualCatalogResponse,
    ManualDetail,
    ManualListResponse,
    ManualSectionChunk,
)


class ManualsRepository(ABC):
    @abstractmethod
    def list(
        self,
        *,
        query: str | None = None,
        tag: str | None = None,
        category: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> ManualListResponse:
        pass

    @abstractmethod
    def get(self, manual_id: str) -> ManualDetail | None:
        pass

    @abstractmethod
    def get_sections(self, manual_id: str) -> builtins.list[ManualSectionChunk]:
        pass

    @abstractmethod
    def get_catalog(self, *, category: str | None = "shogun") -> ManualCatalogResponse:
        pass
