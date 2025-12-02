"""
Artifacts - レポートアーティファクト(Excel/PDF)ストリーミングプロキシ
"""
import logging
import os
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import httpx

from backend_shared.core.domain.exceptions import ExternalServiceError
from backend_shared.application.logging import create_log_context

logger = logging.getLogger(__name__)

router = APIRouter()

LEDGER_API_BASE = os.getenv("LEDGER_API_BASE", "http://ledger_api:8000")


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
    #     raise ForbiddenError(message="Artifact access forbidden")
    
    # ledger_apiの内部論理パス（/reports/artifacts/...）に転送
    upstream_path = f"/reports/artifacts/{report_key}/{date}/{token}/{filename}"
    upstream_url = f"{LEDGER_API_BASE}{upstream_path}"
    
    # クエリパラメータ（signature, expires, disposition）をそのまま転送
    if request.url.query:
        upstream_url += f"?{request.url.query}"
    
    logger.info(
        "[BFF] Proxying artifact request",
        extra=create_log_context(operation="proxy_report_artifact", upstream_url=upstream_url)
    )
    
    # Range, ETag, キャッシュ関連ヘッダーを透過
    passthrough_req_headers = {}
    for header_name in ["range", "if-none-match", "if-modified-since", "authorization"]:
        if header_name in request.headers:
            passthrough_req_headers[header_name] = request.headers[header_name]
            logger.debug(
                "[BFF] Passing request header",
                extra=create_log_context(operation="proxy_report_artifact", header_name=header_name)
            )
    
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
                logger.error(
                    "[BFF] Ledger API returned error",
                    extra=create_log_context(
                        operation="proxy_report_artifact",
                        status_code=upstream_response.status_code
                    )
                )
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
