"""
Manual API Router - BFF for manual_api endpoints
マニュアル検索・閲覧機能のプロキシ
"""
import logging
import os
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse
import httpx

from app.shared.exceptions import ExternalServiceError, ValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/manual", tags=["manual"])

# manual_api のベースURL（環境変数から取得、デフォルトはDocker Compose用）
MANUAL_API_BASE = os.getenv("MANUAL_API_BASE", "http://manual_api:8000")


@router.get("/docs/{doc_id}/{filename:path}")
async def proxy_manual_doc(doc_id: str, filename: str, request: Request):
    """
    マニュアルドキュメント取得（PDF/画像等のストリーミング）
    
    Args:
        doc_id: ドキュメントID
        filename: ファイル名（パス形式も可）
        request: FastAPI Request（クエリパラメータとヘッダを透過）
    
    Returns:
        StreamingResponse: manual_apiからのストリーミングレスポンス
    """
    # クエリパラメータを透過
    upstream = f"{MANUAL_API_BASE}/manual/docs/{doc_id}/{filename}"
    if request.url.query:
        upstream += f"?{request.url.query}"
    
    logger.info(f"[BFF Manual] Proxying doc request: {upstream}")
    
    # 透過するリクエストヘッダ（Range対応、キャッシュ制御）
    req_headers = {}
    for header_key in ["range", "if-none-match", "if-modified-since", "authorization"]:
        if header_key in request.headers:
            req_headers[header_key] = request.headers[header_key]
    
    # タイムアウト設定（大きなファイルの読み込みに対応）
    timeout = httpx.Timeout(60.0, read=300.0)
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("GET", upstream, headers=req_headers) as resp:
                if resp.status_code >= 400:
                    body = await resp.aread()
                    logger.error(f"[BFF Manual] Upstream error: {resp.status_code} - {body.decode(errors='ignore')}")
                    raise ExternalServiceError(
                        service_name="manual_api",
                        message=f"Document retrieval failed: {body.decode(errors='ignore')}",
                        status_code=resp.status_code
                    )
                
                # 透過するレスポンスヘッダ
                res_headers = {}
                for header_key in [
                    "content-type", "content-length", "content-disposition",
                    "etag", "cache-control", "last-modified",
                    "accept-ranges", "content-range"
                ]:
                    if header_key in resp.headers:
                        res_headers[header_key] = resp.headers[header_key]
                
                logger.info(f"[BFF Manual] Streaming doc: {filename}, status={resp.status_code}, content-type={resp.headers.get('content-type')}")
                
                async def iter_bytes():
                    async for chunk in resp.aiter_bytes(chunk_size=65536):
                        yield chunk
                
                return StreamingResponse(
                    iter_bytes(),
                    status_code=resp.status_code,
                    headers=res_headers,
                    media_type=resp.headers.get("content-type", "application/octet-stream")
                )
    
    except httpx.TimeoutException as e:
        logger.error(f"[BFF Manual] Timeout accessing {upstream}")
        raise ExternalServiceError(
            service_name="manual_api",
            message="Gateway timeout",
            cause=e,
            status_code=504
        )
    except httpx.HTTPError as e:
        logger.error(f"[BFF Manual] HTTP error: {str(e)}", exc_info=True)
        raise ExternalServiceError(
            service_name="manual_api",
            message=f"Bad gateway: {str(e)}",
            cause=e,
            status_code=502
        )


@router.post("/search")
async def proxy_manual_search(request: Request):
    """
    マニュアル検索
    
    Args:
        request: FastAPI Request（JSONボディを透過）
    
    Returns:
        JSONResponse: 検索結果
    """
    try:
        payload = await request.json()
    except Exception as e:
        raise ValidationError(message=f"Invalid JSON: {str(e)}", field="request_body")
    
    upstream = f"{MANUAL_API_BASE}/manual/search"
    logger.info(f"[BFF Manual] Proxying search request: {upstream}")
    logger.debug(f"[BFF Manual] Search payload: {payload}")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(upstream, json=payload)
            
            if r.status_code >= 400:
                logger.error(f"[BFF Manual] Search error: {r.status_code} - {r.text}")
                return JSONResponse(
                    status_code=r.status_code,
                    content=r.json() if r.headers.get("content-type") == "application/json" else {"error": r.text}
                )
            
            logger.info(f"[BFF Manual] Search success: {r.status_code}")
            return JSONResponse(status_code=r.status_code, content=r.json())
    
    except httpx.HTTPError as e:
        logger.error(f"[BFF Manual] HTTP error: {str(e)}", exc_info=True)
        raise ExternalServiceError(
            service_name="manual_api",
            message=f"Search request failed: {str(e)}",
            cause=e,
            status_code=502
        )


@router.get("/toc")
async def proxy_manual_toc():
    """
    マニュアル目次取得
    
    Returns:
        JSON: 目次データ
    """
    upstream = f"{MANUAL_API_BASE}/manual/toc"
    logger.info(f"[BFF Manual] Proxying toc request: {upstream}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(upstream)
            r.raise_for_status()
            logger.info(f"[BFF Manual] TOC success: {r.status_code}")
            return r.json()
    
    except httpx.HTTPStatusError as e:
        logger.error(f"[BFF Manual] TOC error: {e.response.status_code}", exc_info=True)
        raise ExternalServiceError(
            service_name="manual_api",
            message="TOC retrieval failed",
            cause=e,
            status_code=e.response.status_code
        )
    except httpx.HTTPError as e:
        logger.error(f"[BFF Manual] HTTP error: {str(e)}", exc_info=True)
        raise ExternalServiceError(
            service_name="manual_api",
            message=f"Bad gateway: {str(e)}",
            cause=e,
            status_code=502
        )


@router.get("/categories")
async def proxy_manual_categories():
    """
    マニュアルカテゴリ一覧取得
    
    Returns:
        JSON: カテゴリデータ
    """
    upstream = f"{MANUAL_API_BASE}/manual/categories"
    logger.info(f"[BFF Manual] Proxying categories request: {upstream}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(upstream)
            r.raise_for_status()
            logger.info(f"[BFF Manual] Categories success: {r.status_code}")
            return r.json()
    
    except httpx.HTTPStatusError as e:
        logger.error(f"[BFF Manual] Categories error: {e.response.status_code}", exc_info=True)
        raise ExternalServiceError(
            service_name="manual_api",
            message="Categories retrieval failed",
            cause=e,
            status_code=e.response.status_code
        )
    except httpx.HTTPError as e:
        logger.error(f"[BFF Manual] HTTP error: {str(e)}", exc_info=True)
        raise ExternalServiceError(
            service_name="manual_api",
            message=f"Bad gateway: {str(e)}",
            cause=e,
            status_code=502
        )


# ============================================================================
# Legacy endpoints (for compatibility with existing frontend code)
# ============================================================================

@router.get("/manuals")
async def proxy_list_manuals(request: Request):
    """
    マニュアル一覧取得（レガシー互換）
    
    Query params: query, tag, category, page, size
    """
    upstream = f"{MANUAL_API_BASE}/manual/manuals"
    if request.url.query:
        upstream += f"?{request.url.query}"
    
    logger.info(f"[BFF Manual] Proxying list manuals: {upstream}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(upstream)
            r.raise_for_status()
            logger.info(f"[BFF Manual] List manuals success: {r.status_code}")
            return r.json()
    
    except httpx.HTTPStatusError as e:
        logger.error(f"[BFF Manual] List manuals error: {e.response.status_code}", exc_info=True)
        raise ExternalServiceError(
            service_name="manual_api",
            message="List manuals failed",
            cause=e,
            status_code=e.response.status_code
        )
    except httpx.HTTPError as e:
        logger.error(f"[BFF Manual] HTTP error: {str(e)}", exc_info=True)
        raise ExternalServiceError(
            service_name="manual_api",
            message=f"Bad gateway: {str(e)}",
            cause=e,
            status_code=502
        )


@router.get("/manuals/catalog")
async def proxy_manual_catalog(request: Request):
    """
    マニュアルカタログ取得（レガシー互換）
    
    Query params: category
    """
    upstream = f"{MANUAL_API_BASE}/manual/manuals/catalog"
    if request.url.query:
        upstream += f"?{request.url.query}"
    
    logger.info(f"[BFF Manual] Proxying catalog: {upstream}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(upstream)
            r.raise_for_status()
            logger.info(f"[BFF Manual] Catalog success: {r.status_code}")
            return r.json()
    
    except httpx.HTTPStatusError as e:
        logger.error(f"[BFF Manual] Catalog error: {e.response.status_code}", exc_info=True)
        raise ExternalServiceError(
            service_name="manual_api",
            message="Catalog retrieval failed",
            cause=e,
            status_code=e.response.status_code
        )
    except httpx.HTTPError as e:
        logger.error(f"[BFF Manual] HTTP error: {str(e)}", exc_info=True)
        raise ExternalServiceError(
            service_name="manual_api",
            message=f"Bad gateway: {str(e)}",
            cause=e,
            status_code=502
        )


@router.get("/manuals/{manual_id}")
async def proxy_manual_detail(manual_id: str):
    """
    マニュアル詳細取得（レガシー互換）
    """
    upstream = f"{MANUAL_API_BASE}/manual/manuals/{manual_id}"
    logger.info(f"[BFF Manual] Proxying manual detail: {upstream}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(upstream)
            r.raise_for_status()
            logger.info(f"[BFF Manual] Manual detail success: {r.status_code}")
            return r.json()
    
    except httpx.HTTPStatusError as e:
        logger.error(f"[BFF Manual] Manual detail error: {e.response.status_code}", exc_info=True)
        raise ExternalServiceError(
            service_name="manual_api",
            message="Manual detail retrieval failed",
            cause=e,
            status_code=e.response.status_code
        )
    except httpx.HTTPError as e:
        logger.error(f"[BFF Manual] HTTP error: {str(e)}", exc_info=True)
        raise ExternalServiceError(
            service_name="manual_api",
            message=f"Bad gateway: {str(e)}",
            cause=e,
            status_code=502
        )


@router.get("/manuals/{manual_id}/sections")
async def proxy_manual_sections(manual_id: str):
    """
    マニュアルセクション取得（レガシー互換）
    """
    upstream = f"{MANUAL_API_BASE}/manual/manuals/{manual_id}/sections"
    logger.info(f"[BFF Manual] Proxying manual sections: {upstream}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(upstream)
            r.raise_for_status()
            logger.info(f"[BFF Manual] Manual sections success: {r.status_code}")
            return r.json()
    
    except httpx.HTTPStatusError as e:
        logger.error(f"[BFF Manual] Manual sections error: {e.response.status_code}", exc_info=True)
        raise ExternalServiceError(
            service_name="manual_api",
            message="Manual sections retrieval failed",
            cause=e,
            status_code=e.response.status_code
        )
    except httpx.HTTPError as e:
        logger.error(f"[BFF Manual] HTTP error: {str(e)}", exc_info=True)
        raise ExternalServiceError(
            service_name="manual_api",
            message=f"Bad gateway: {str(e)}",
            cause=e,
            status_code=502
        )
