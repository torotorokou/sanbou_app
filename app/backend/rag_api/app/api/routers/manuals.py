from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Depends

from app.core.domain.manuals.manual_entity import ManualDetail, ManualListResponse
from app.core.usecases.manuals.manuals_service import ManualsService
from app.api.dependencies import get_manuals_service


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


@router.get("/{manual_id}", response_model=ManualDetail)
def get_manual(manual_id: str, service: ManualsService = Depends(get_manuals_service)):
    m = service.get(manual_id)
    if not m:
        raise HTTPException(status_code=404, detail="manual not found")
    return m


@router.get("/{manual_id}/sections")
def get_manual_sections(manual_id: str, service: ManualsService = Depends(get_manuals_service)):
    m = service.get(manual_id)
    if not m:
        raise HTTPException(status_code=404, detail="manual not found")
    return service.get_sections(manual_id)
