from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.api.schemas.manuals import ManualDetail, ManualListResponse
from app.core.usecases.manuals_service import ManualsService


router = APIRouter(prefix="/manuals", tags=["manuals"])
service = ManualsService()


@router.get("", response_model=ManualListResponse)
def list_manuals(
    query: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    category: str | None = Query(default="shogun"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    return service.list(query=query, tag=tag, category=category, page=page, size=size)


@router.get("/{manual_id}", response_model=ManualDetail)
def get_manual(manual_id: str):
    m = service.get(manual_id)
    if not m:
        raise HTTPException(status_code=404, detail="manual not found")
    return m


@router.get("/{manual_id}/sections")
def get_manual_sections(manual_id: str):
    m = service.get(manual_id)
    if not m:
        raise HTTPException(status_code=404, detail="manual not found")
    return service.get_sections(manual_id)
