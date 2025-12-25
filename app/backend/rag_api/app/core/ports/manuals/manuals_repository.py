from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.domain.manuals.manual_entity import (
    ManualDetail,
    ManualListResponse,
    ManualSectionChunk,
)


class ManualsRepository(ABC):
    @abstractmethod
    def list(
        self,
        *,
        query: Optional[str] = None,
        tag: Optional[str] = None,
        category: Optional[str] = None,
        page: int = 1,
        size: int = 20,
    ) -> ManualListResponse:
        pass

    @abstractmethod
    def get(self, manual_id: str) -> Optional[ManualDetail]:
        pass

    @abstractmethod
    def get_sections(self, manual_id: str) -> List[ManualSectionChunk]:
        pass
