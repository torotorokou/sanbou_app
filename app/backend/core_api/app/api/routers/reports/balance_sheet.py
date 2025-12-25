"""
Balance Sheet - 収支表生成エンドポイント
"""

import os

import httpx
from fastapi import APIRouter, Request

from app.shared.utils import rewrite_artifact_urls_to_bff
from backend_shared.application.logging import create_log_context, get_module_logger
from backend_shared.core.domain.exceptions import ExternalServiceError

logger = get_module_logger(__name__)

router = APIRouter()

LEDGER_API_BASE = os.getenv("LEDGER_API_BASE", "http://ledger_api:8000")


@router.post("/balance_sheet/")
async def proxy_balance_sheet(request: Request):
    """収支表生成（ledger_apiへフォワード）- FormData対応"""
    logger.info(
        "Proxying balance_sheet request (FormData)",
        extra=create_log_context(
            operation="proxy_balance_sheet", client=str(request.client)
        ),
    )
    try:
        form = await request.form()
        logger.info(f"Received form keys: {list(form.keys())}")

        files = {}
        data = {}
        for key, value in form.items():
            if hasattr(value, "read"):
                from starlette.datastructures import UploadFile

                if isinstance(value, UploadFile):
                    content = await value.read()
                    files[key] = (value.filename, content, value.content_type)
                    logger.info(
                        f"File '{key}': {value.filename} ({len(content)} bytes)"
                    )
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
            cause=e,
        )
    except httpx.HTTPError as e:
        logger.error(f"Failed to reach ledger_api: {str(e)}")
        raise ExternalServiceError(
            service_name="ledger_api",
            message=f"Cannot reach ledger_api: {str(e)}",
            cause=e,
        )
