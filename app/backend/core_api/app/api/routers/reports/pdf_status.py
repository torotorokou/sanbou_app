"""
PDF Status - PDFステータス確認エンドポイント
Excel同期+PDF非同期構成でのポーリング用
"""

import os
from typing import Literal, Optional

import httpx
from app.shared.utils import rewrite_artifact_urls_to_bff
from backend_shared.application.logging import create_log_context, get_module_logger
from backend_shared.core.domain.exceptions import ExternalServiceError
from fastapi import APIRouter, Query
from pydantic import BaseModel

logger = get_module_logger(__name__)

router = APIRouter()

LEDGER_API_BASE = os.getenv("LEDGER_API_BASE", "http://ledger_api:8000")


class PdfStatusResponse(BaseModel):
    """PDFステータスレスポンス"""

    report_key: str
    report_token: str
    status: Literal["pending", "ready", "error"]
    pdf_url: Optional[str] = None
    message: Optional[str] = None


@router.get("/pdf-status")
async def proxy_pdf_status(
    report_key: str = Query(..., description="レポートキー（例: factory_report）"),
    report_date: str = Query(..., description="レポート日付（例: 2025-12-11）"),
    report_token: str = Query(..., description="レポートトークン"),
) -> PdfStatusResponse:
    """
    PDFステータス確認（ledger_apiへフォワード）

    フロントエンドからポーリングで呼ばれ、PDF生成完了を確認する。
    """
    logger.debug(
        "Proxying PDF status check",
        extra=create_log_context(
            operation="proxy_pdf_status",
            report_key=report_key,
            report_date=report_date,
            report_token=report_token,
        ),
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"{LEDGER_API_BASE}/reports/pdf-status"
            params = {
                "report_key": report_key,
                "report_date": report_date,
                "report_token": report_token,
            }

            logger.debug(f"Forwarding PDF status check to {url}")
            r = await client.get(url, params=params)
            r.raise_for_status()

            # BFFの責務: 内部論理パスを外向きパスに変換
            response_data = r.json()
            response_data = rewrite_artifact_urls_to_bff(response_data)
            return PdfStatusResponse(**response_data)

    except httpx.HTTPStatusError as e:
        logger.error(
            f"Ledger API returned error: {e.response.status_code}",
            extra=create_log_context(
                operation="proxy_pdf_status",
                error=e.response.text[:200],
            ),
            exc_info=True,
        )
        raise ExternalServiceError(
            service_name="ledger_api",
            message=f"PDF status check failed: {e.response.text[:200]}",
            status_code=e.response.status_code,
            cause=e,
        )
    except httpx.HTTPError as e:
        logger.error(
            f"Failed to reach ledger_api: {str(e)}",
            extra=create_log_context(operation="proxy_pdf_status"),
            exc_info=True,
        )
        raise ExternalServiceError(
            service_name="ledger_api",
            message=f"Cannot reach ledger_api: {str(e)}",
            cause=e,
        )
