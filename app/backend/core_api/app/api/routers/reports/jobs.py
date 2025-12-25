"""
Jobs - ジョブステータス・通知ストリームエンドポイント
"""

import os

import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend_shared.application.logging import create_log_context, get_module_logger
from backend_shared.core.domain.exceptions import ExternalServiceError

logger = get_module_logger(__name__)

router = APIRouter()

LEDGER_API_BASE = os.getenv("LEDGER_API_BASE", "http://ledger_api:8000")


@router.get("/notifications/stream")
async def proxy_notifications_stream():
    """SSE通知ストリーム（ledger_apiへフォワード）"""
    logger.info("Proxying notifications/stream request")

    async def stream_generator():
        try:
            async with httpx.AsyncClient(
                timeout=None
            ) as client:  # SSEは長時間接続なのでtimeout無し
                url = f"{LEDGER_API_BASE}/notifications/stream"
                async with client.stream("GET", url) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes():
                        yield chunk
        except httpx.HTTPError as e:
            logger.error(f"Failed to stream from ledger_api: {str(e)}")
            yield b'data: {"error": "LEDGER_UNREACHABLE"}\n\n'

    return StreamingResponse(stream_generator(), media_type="text/event-stream")


@router.get("/jobs/{job_id}")
async def proxy_job_status(job_id: str):
    """ジョブステータス取得（ledger_apiへフォワード）"""
    logger.info(
        "Proxying job status request",
        extra=create_log_context(operation="proxy_job_status", job_id=job_id),
    )
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
            cause=e,
        )
    except httpx.HTTPError as e:
        raise ExternalServiceError(
            service_name="ledger_api",
            message=f"Cannot reach ledger_api: {str(e)}",
            cause=e,
        )
