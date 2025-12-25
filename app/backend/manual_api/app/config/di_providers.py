from functools import lru_cache

from app.core.ports.manuals_repository import ManualsRepository
from app.core.usecases.manuals_service import ManualsService
from app.infra.adapters.manuals_repository import InMemoryManualRepository


@lru_cache
def get_manuals_repository() -> ManualsRepository:
    return InMemoryManualRepository()


@lru_cache
def get_manuals_service() -> ManualsService:
    return ManualsService(repo=get_manuals_repository())
