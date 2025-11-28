from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Body
from .service import ManualsService
from .schemas import ManualDetail, ManualListResponse, ManualCatalogResponse, SearchRequest


router = APIRouter(tags=["manuals"])
service = ManualsService()


# Frontend expects: POST /manual/search
@router.post("/search")
def search_manuals(request: SearchRequest = Body(...)):
    """
    マニュアル検索エンドポイント
    フロントエンドからのPOSTリクエストを受け付ける
    """
    return service.list(
        query=request.query,
        tag=request.tag,
        category=request.category,
        page=request.page,
        size=request.limit or 20
    )


# Frontend expects: GET /manual/toc
@router.get("/toc")
def get_table_of_contents(category: str | None = Query(default="shogun")):
    """
    マニュアル目次取得エンドポイント
    """
    return service.get_catalog(category=category)


# Frontend expects: GET /manual/categories
@router.get("/categories")
def get_categories():
    """
    カテゴリ一覧取得エンドポイント
    """
    # TODO: 実際のカテゴリデータを返す実装
    return {"categories": [{"id": "shogun", "name": "将軍システム"}]}


# 既存のエンドポイント（互換性のため残す）
@router.get("/manuals", response_model=ManualListResponse)
def list_manuals(
    query: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    category: str | None = Query(default="shogun"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    return service.list(query=query, tag=tag, category=category, page=page, size=size)


@router.get("/manuals/catalog", response_model=ManualCatalogResponse)
def get_manual_catalog(category: str | None = Query(default="shogun")):
    return service.get_catalog(category=category)


@router.get("/manuals/{manual_id}", response_model=ManualDetail)
def get_manual(manual_id: str):
    m = service.get(manual_id)
    if not m:
        raise HTTPException(status_code=404, detail="manual not found")
    return m


@router.get("/manuals/{manual_id}/sections")
def get_manual_sections(manual_id: str):
    m = service.get(manual_id)
    if not m:
        raise HTTPException(status_code=404, detail="manual not found")
    return service.get_sections(manual_id)
