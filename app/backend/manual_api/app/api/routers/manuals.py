from __future__ import annotations

from app.config.di_providers import get_manuals_service
from app.core.domain.manual_entity import (
    ManualCatalogResponse,
    ManualDetail,
    ManualListResponse,
)
from app.core.usecases.manuals_service import ManualsService
from backend_shared.application.logging import get_module_logger
from backend_shared.core.domain.exceptions import NotFoundError
from fastapi import APIRouter, Depends, Query

logger = get_module_logger(__name__)
router = APIRouter(prefix="/manuals", tags=["manuals"])


@router.get("", response_model=ManualListResponse)
def list_manuals(
    query: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    category: str | None = Query(default="shogun"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    service: ManualsService = Depends(get_manuals_service),
):
    return service.list(query=query, tag=tag, category=category, page=page, size=size)


@router.get("/catalog", response_model=ManualCatalogResponse)
def get_manual_catalog(
    category: str | None = Query(default="shogun"),
    service: ManualsService = Depends(get_manuals_service),
):
    return service.get_catalog(category=category)


@router.get("/{manual_id}", response_model=ManualDetail)
def get_manual(
    manual_id: str,
    service: ManualsService = Depends(get_manuals_service),
):
    m = service.get(manual_id)
    if not m:
        raise NotFoundError("Manual", manual_id)
    return m


@router.get("/{manual_id}/sections")
def get_manual_sections(
    manual_id: str,
    service: ManualsService = Depends(get_manuals_service),
):
    m = service.get(manual_id)
    if not m:
        raise NotFoundError("Manual", manual_id)
    return service.get_sections(manual_id)
