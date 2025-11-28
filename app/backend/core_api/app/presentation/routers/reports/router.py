"""
Reports Router - BFF for ledger_api report endpoints
フロントエンドからの全レポートリクエストを受け、ledger_apiに転送

設計方針:
  - カスタム例外を使用(HTTPExceptionは使用しない)
  - ExternalServiceError で外部サービスエラーをラップ
"""
import logging
import os
from typing import Any, Dict, Optional
from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx

from app.shared.exceptions import ExternalServiceError
from app.shared.utils import rewrite_artifact_urls_to_bff

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])

# ledger_api のベースURL（環境変数から取得、デフォルトはDocker Compose用）
LEDGER_API_BASE = os.getenv("LEDGER_API_BASE", "http://ledger_api:8000")


class FactoryReportPayload(BaseModel):
    """工場日報生成リクエスト"""
    date: str
    factory_id: Optional[str] = None


class BalanceSheetPayload(BaseModel):
    """収支表生成リクエスト"""
    date: str
    factory_id: Optional[str] = None


class AverageSheetPayload(BaseModel):
    """平均表生成リクエスト"""
    date: str
    factory_id: Optional[str] = None


class ManagementSheetPayload(BaseModel):
    """管理表生成リクエスト"""
    date: str
    factory_id: Optional[str] = None


class BlockUnitPricePayload(BaseModel):
    """ブロック単価初期化リクエスト"""
    date: str
    factory_id: Optional[str] = None


@router.post("/factory_report/")
async def proxy_factory_report(request: Request):
    """
    工場日報生成（ledger_apiへフォワード）
    FormDataをそのまま転送
    """
    logger.info(f"Proxying factory_report request (FormData) from {request.client}")
    logger.info(f"Request headers: {dict(request.headers)}")
    try:
        # FormDataをそのまま読み取り
        form = await request.form()
        logger.info(f"Received form keys: {list(form.keys())}")
        
        # FormDataを再構築してledger_apiに送信
        files = {}
        data = {}
        for key, value in form.items():
            if hasattr(value, 'read'):  # ファイルオブジェクト（UploadFile）
                # UploadFileの場合、ファイル内容を読み取って送信
                from starlette.datastructures import UploadFile
                if isinstance(value, UploadFile):
                    content = await value.read()
                    files[key] = (value.filename, content, value.content_type)
                    logger.info(f"File '{key}': {value.filename} ({len(content)} bytes)")
            else:
                data[key] = value
                logger.info(f"Data '{key}': {value}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            url = f"{LEDGER_API_BASE}/reports/factory_report/"
            logger.info(f"Forwarding to {url}")
            logger.info(f"  - data keys: {list(data.keys())}")
            logger.info(f"  - file keys: {list(files.keys())}")
            r = await client.post(url, data=data, files=files)
            logger.info(f"Ledger API response: {r.status_code}")
            r.raise_for_status()
            
            # BFFの責務: 内部論理パスを外向きパスに変換
            response_data = r.json()
            return rewrite_artifact_urls_to_bff(response_data)
    except httpx.HTTPStatusError as e:
        logger.error(f"Ledger API returned error: {e.response.status_code} - {e.response.text}", exc_info=True)
        raise ExternalServiceError(
            service_name="ledger_api",
            message=f"Factory report generation failed: {e.response.text[:200]}",
            status_code=e.response.status_code,
            cause=e
        )
    except httpx.HTTPError as e:
        logger.error(f"Failed to reach ledger_api: {str(e)}", exc_info=True)
        raise ExternalServiceError(
            service_name="ledger_api",
            message=f"Cannot reach ledger_api: {str(e)}",
            cause=e
        )


@router.get("/artifacts/{report_key}/{date}/{token}/{filename}")
async def proxy_artifact(
    report_key: str,
    date: str,
    token: str, 
    filename: str,
    request: Request
):
    """
    レポートアーティファクト（Excel/PDF）の取得をledger_apiにプロキシ
    
    BFFの責務:
    - 認可/認証のゲートウェイ（必要に応じて実装）
    - ストリーミング中継（大容量対応）
    - ヘッダー透過（Content-Type, Range, ETag, Cache-Control等）
    - URLパスは書き換えず、ledger_apiの内部論理パスをそのまま使用
    
    Args:
        report_key: レポートタイプ（例: factory_report）
        date: レポート期間（例: 2025-10-01）
        token: レポートトークン（タイムスタンプ+UUID）
        filename: ファイル名（例: factory_report-2025-10-01.pdf）
        request: クエリパラメータ（expires, signature, disposition）を含むリクエスト
    
    Returns:
        StreamingResponse: ledger_apiからのストリーミングレスポンス
    """
    # TODO: ここでユーザー認可/トークン検証を実施（BFFの責務）
    # if not await authorize_user(request):
    #     raise HTTPException(status_code=403, detail="Forbidden")
    
    # ledger_apiの内部論理パス（/reports/artifacts/...）に転送
    upstream_path = f"/reports/artifacts/{report_key}/{date}/{token}/{filename}"
    upstream_url = f"{LEDGER_API_BASE}{upstream_path}"
    
    # クエリパラメータ（signature, expires, disposition）をそのまま転送
    if request.url.query:
        upstream_url += f"?{request.url.query}"
    
    logger.info(f"[BFF] Proxying artifact request to {upstream_url}")
    
    # Range, ETag, キャッシュ関連ヘッダーを透過
    passthrough_req_headers = {}
    for header_name in ["range", "if-none-match", "if-modified-since", "authorization"]:
        if header_name in request.headers:
            passthrough_req_headers[header_name] = request.headers[header_name]
            logger.debug(f"[BFF] Passing request header: {header_name}")
    
    try:
        timeout = httpx.Timeout(60.0, read=300.0)  # 大容量ファイル対応
        async with httpx.AsyncClient(timeout=timeout) as client:
            upstream_response = await client.get(
                upstream_url, 
                headers=passthrough_req_headers,
                follow_redirects=False  # リダイレクトは透過
            )
            
            # エラーレスポンスはそのまま返す
            if upstream_response.status_code >= 400:
                body = await upstream_response.aread()
                logger.error(f"[BFF] Ledger API returned error: {upstream_response.status_code}")
                raise ExternalServiceError(
                    service_name="ledger_api",
                    message=f"Artifact download failed: {body.decode(errors='ignore')[:200]}",
                    status_code=upstream_response.status_code
                )
            
            # レスポンスヘッダーを透過（Content-Type, Content-Disposition等）
            passthrough_res_headers = {}
            for header_name in [
                "content-type",
                "content-length", 
                "content-disposition",
                "etag",
                "cache-control",
                "last-modified",
                "accept-ranges",
                "content-range",  # Range request の場合
            ]:
                if header_name in upstream_response.headers:
                    passthrough_res_headers[header_name] = upstream_response.headers[header_name]
            
            logger.info(
                f"[BFF] Streaming artifact: {filename}, "
                f"status={upstream_response.status_code}, "
                f"content-type={passthrough_res_headers.get('content-type')}"
            )
            
            # ストリーミングレスポンス（メモリ効率的）
            async def iter_stream():
                async for chunk in upstream_response.aiter_bytes(chunk_size=65536):  # 64KB chunks
                    yield chunk
            
            return StreamingResponse(
                content=iter_stream(),
                status_code=upstream_response.status_code,
                headers=passthrough_res_headers,
                media_type=upstream_response.headers.get("content-type", "application/octet-stream")
            )
            
    except httpx.TimeoutException as e:
        logger.error(f"[BFF] Timeout while fetching artifact: {str(e)}")
        raise ExternalServiceError(
            service_name="ledger_api",
            message=f"Artifact download timeout: {str(e)}",
            status_code=504,
            cause=e
        )
    except httpx.HTTPError as e:
        logger.error(f"[BFF] HTTP error while fetching artifact: {str(e)}")
        raise ExternalServiceError(
            service_name="ledger_api",
            message=f"Artifact download failed: {str(e)}",
            cause=e
        )


@router.post("/balance_sheet/")
async def proxy_balance_sheet(request: Request):
    """収支表生成（ledger_apiへフォワード）- FormData対応"""
    logger.info(f"Proxying balance_sheet request (FormData) from {request.client}")
    try:
        form = await request.form()
        logger.info(f"Received form keys: {list(form.keys())}")
        
        files = {}
        data = {}
        for key, value in form.items():
            if hasattr(value, 'read'):
                from starlette.datastructures import UploadFile
                if isinstance(value, UploadFile):
                    content = await value.read()
                    files[key] = (value.filename, content, value.content_type)
                    logger.info(f"File '{key}': {value.filename} ({len(content)} bytes)")
            else:
                data[key] = value
                logger.info(f"Data '{key}': {value}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            url = f"{LEDGER_API_BASE}/reports/balance_sheet/"
            logger.info(f"Forwarding to {url}")
            r = await client.post(url, data=data, files=files)
            logger.info(f"Ledger API response: {r.status_code}")
            r.raise_for_status()
            return rewrite_artifact_urls_to_bff(r.json())
    except httpx.HTTPStatusError as e:
        logger.error(f"Ledger API returned error: {e.response.status_code}")
        raise ExternalServiceError(
            service_name="ledger_api",
            message=f"Balance sheet generation failed: {str(e)}",
            status_code=e.response.status_code,
            cause=e
        )
    except httpx.HTTPError as e:
        logger.error(f"Failed to reach ledger_api: {str(e)}")
        raise ExternalServiceError(
            service_name="ledger_api",
            message=f"Cannot reach ledger_api: {str(e)}",
            cause=e
        )


@router.post("/average_sheet/")
async def proxy_average_sheet(request: Request):
    """平均表生成（ledger_apiへフォワード）- FormData対応"""
    logger.info(f"Proxying average_sheet request (FormData) from {request.client}")
    try:
        form = await request.form()
        logger.info(f"Received form keys: {list(form.keys())}")
        
        files = {}
        data = {}
        for key, value in form.items():
            if hasattr(value, 'read'):
                from starlette.datastructures import UploadFile
                if isinstance(value, UploadFile):
                    content = await value.read()
                    files[key] = (value.filename, content, value.content_type)
                    logger.info(f"File '{key}': {value.filename} ({len(content)} bytes)")
            else:
                data[key] = value
                logger.info(f"Data '{key}': {value}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            url = f"{LEDGER_API_BASE}/reports/average_sheet/"
            logger.info(f"Forwarding to {url}")
            logger.info(f"  - data keys: {list(data.keys())}")
            logger.info(f"  - file keys: {list(files.keys())}")
            r = await client.post(url, data=data, files=files)
            logger.info(f"Ledger API response: {r.status_code}")
            r.raise_for_status()
            return rewrite_artifact_urls_to_bff(r.json())
    except httpx.HTTPStatusError as e:
        logger.error(f"Ledger API returned error: {e.response.status_code} - {e.response.text}", exc_info=True)
        raise ExternalServiceError(
            service_name="ledger_api",
            message=f"Average sheet generation failed: {e.response.text[:200]}",
            status_code=e.response.status_code,
            cause=e
        )
    except httpx.HTTPError as e:
        logger.error(f"Failed to reach ledger_api: {str(e)}", exc_info=True)
        raise ExternalServiceError(
            service_name="ledger_api",
            message=f"Cannot reach ledger_api: {str(e)}",
            cause=e
        )


@router.post("/management_sheet/")
async def proxy_management_sheet(request: Request):
    """管理表生成（ledger_apiへフォワード）- FormData対応"""
    logger.info(f"Proxying management_sheet request (FormData) from {request.client}")
    try:
        form = await request.form()
        logger.info(f"Received form keys: {list(form.keys())}")
        
        files = {}
        data = {}
        for key, value in form.items():
            if hasattr(value, 'read'):
                from starlette.datastructures import UploadFile
                if isinstance(value, UploadFile):
                    content = await value.read()
                    files[key] = (value.filename, content, value.content_type)
                    logger.info(f"File '{key}': {value.filename} ({len(content)} bytes)")
            else:
                data[key] = value
                logger.info(f"Data '{key}': {value}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            url = f"{LEDGER_API_BASE}/reports/management_sheet/"
            logger.info(f"Forwarding to {url}")
            r = await client.post(url, data=data, files=files)
            logger.info(f"Ledger API response: {r.status_code}")
            r.raise_for_status()
            return rewrite_artifact_urls_to_bff(r.json())
    except httpx.HTTPStatusError as e:
        raise ExternalServiceError(
            service_name="ledger_api",
            message=f"Management sheet generation failed: {str(e)}",
            status_code=e.response.status_code,
            cause=e
        )
    except httpx.HTTPError as e:
        raise ExternalServiceError(
            service_name="ledger_api",
            message=f"Cannot reach ledger_api: {str(e)}",
            cause=e
        )


# 通知ストリームエンドポイント
@router.get("/notifications/stream")
async def proxy_notifications_stream():
    """SSE通知ストリーム（ledger_apiへフォワード）"""
    logger.info("Proxying notifications/stream request")
    
    async def stream_generator():
        try:
            async with httpx.AsyncClient(timeout=None) as client:  # SSEは長時間接続なのでtimeout無し
                url = f"{LEDGER_API_BASE}/notifications/stream"
                async with client.stream("GET", url) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes():
                        yield chunk
        except httpx.HTTPError as e:
            logger.error(f"Failed to stream from ledger_api: {str(e)}")
            yield f"data: {{\"error\": \"LEDGER_UNREACHABLE\"}}\n\n".encode()
    
    return StreamingResponse(stream_generator(), media_type="text/event-stream")


# ジョブステータスエンドポイント
@router.get("/jobs/{job_id}")
async def proxy_job_status(job_id: str):
    """ジョブステータス取得（ledger_apiへフォワード）"""
    logger.info(f"Proxying job status request for job_id: {job_id}")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{LEDGER_API_BASE}/api/jobs/{job_id}"
            r = await client.get(url)
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        raise ExternalServiceError(
            service_name="ledger_api",
            message=f"Job status fetch failed: {str(e)}",
            status_code=e.response.status_code,
            cause=e
        )
    except httpx.HTTPError as e:
        raise ExternalServiceError(
            service_name="ledger_api",
            message=f"Cannot reach ledger_api: {str(e)}",
            cause=e
        )

