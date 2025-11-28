"""
Block Unit Price Router - BFF for ledger_api block_unit_price_interactive endpoints
インタラクティブな帳簿生成フローをプロキシ

設計方針:
  - カスタム例外を使用(HTTPExceptionは使用しない)
  - ExternalServiceError で外部サービスエラーをラップ
"""
import logging
import os
from typing import Any, Dict, Optional
from fastapi import APIRouter, Request, UploadFile, File, Form
import httpx

from backend_shared.core.domain.exceptions import ExternalServiceError
from app.shared.utils import rewrite_artifact_urls_to_bff

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/block_unit_price_interactive", tags=["block_unit_price"])

# ledger_api のベースURL（環境変数から取得、デフォルトはDocker Compose用）
LEDGER_API_BASE = os.getenv("LEDGER_API_BASE", "http://ledger_api:8000")


@router.post("/initial")
async def proxy_block_unit_price_initial(
    request: Request,
    shipment: Optional[UploadFile] = File(None),
):
    """
    ブロック単価初期化（ledger_apiへフォワード）
    フロントから /core_api/block_unit_price_interactive/initial へのリクエストを受け取る
    FormDataとして送信されたファイルを ledger_api に転送
    """
    logger.info(f"Proxying block_unit_price_interactive/initial request from {request.client}")
    try:
        files = {}
        
        if shipment:
            # ファイルを読み込んで転送用に準備
            file_content = await shipment.read()
            files["shipment"] = (shipment.filename, file_content, shipment.content_type)
            logger.info(f"File 'shipment': {shipment.filename} ({len(file_content)} bytes)")
        else:
            logger.warning("No shipment file provided")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # ledger_apiの実エンドポイント（内部論理パス）
            url = f"{LEDGER_API_BASE}/block_unit_price_interactive/initial"
            logger.info(f"Forwarding to {url}")
            r = await client.post(url, files=files)
            logger.info(f"Ledger API response: {r.status_code}")
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Ledger API returned error: {e.response.status_code} - {e.response.text}", exc_info=True)
        raise ExternalServiceError(
            service_name="ledger_api",
            message=f"Block unit price initial failed: {e.response.text[:200]}",
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


@router.post("/start")
async def proxy_block_unit_price_start(request: Request):
    """ブロック単価処理開始（ledger_apiへフォワード）"""
    logger.info("Proxying block_unit_price_interactive/start request")
    try:
        body = await request.json()
        async with httpx.AsyncClient(timeout=60.0) as client:
            url = f"{LEDGER_API_BASE}/block_unit_price_interactive/start"
            logger.info(f"Forwarding to {url}")
            r = await client.post(url, json=body)
            logger.info(f"Ledger API response: {r.status_code}")
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Ledger API error: {e.response.status_code}", exc_info=True)
        raise ExternalServiceError(
            service_name="ledger_api",
            message=f"Block unit price start failed: {str(e)}",
            status_code=e.response.status_code,
            cause=e
        )
    except httpx.HTTPError as e:
        logger.error(f"HTTP error: {str(e)}", exc_info=True)
        raise ExternalServiceError(
            service_name="ledger_api",
            message=f"Cannot reach ledger_api: {str(e)}",
            cause=e
        )


@router.post("/select-transport")
async def proxy_block_unit_price_select_transport(request: Request):
    """ブロック単価輸送選択（ledger_apiへフォワード）"""
    logger.info("Proxying block_unit_price_interactive/select-transport request")
    try:
        body = await request.json()
        async with httpx.AsyncClient(timeout=60.0) as client:
            url = f"{LEDGER_API_BASE}/block_unit_price_interactive/select-transport"
            logger.info(f"Forwarding to {url}")
            r = await client.post(url, json=body)
            logger.info(f"Ledger API response: {r.status_code}")
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Ledger API error: {e.response.status_code}", exc_info=True)
        raise ExternalServiceError(
            service_name="ledger_api",
            message=f"Transport selection failed: {str(e)}",
            status_code=e.response.status_code,
            cause=e
        )
    except httpx.HTTPError as e:
        logger.error(f"HTTP error: {str(e)}", exc_info=True)
        raise ExternalServiceError(
            service_name="ledger_api",
            message=f"Cannot reach ledger_api: {str(e)}",
            cause=e
        )


@router.post("/apply")
async def proxy_block_unit_price_apply(request: Request):
    """ブロック単価適用（ledger_apiへフォワード）"""
    logger.info("Proxying block_unit_price_interactive/apply request")
    try:
        body = await request.json()
        async with httpx.AsyncClient(timeout=60.0) as client:
            url = f"{LEDGER_API_BASE}/block_unit_price_interactive/apply"
            logger.info(f"Forwarding to {url}")
            r = await client.post(url, json=body)
            logger.info(f"Ledger API response: {r.status_code}")
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Ledger API error: {e.response.status_code}", exc_info=True)
        raise ExternalServiceError(
            service_name="ledger_api",
            message=f"Block unit price apply failed: {str(e)}",
            status_code=e.response.status_code,
            cause=e
        )
    except httpx.HTTPError as e:
        logger.error(f"HTTP error: {str(e)}", exc_info=True)
        raise ExternalServiceError(
            service_name="ledger_api",
            message=f"Cannot reach ledger_api: {str(e)}",
            cause=e
        )


@router.post("/finalize")
async def proxy_block_unit_price_finalize(request: Request):
    """ブロック単価確定（ledger_apiへフォワード）"""
    logger.info("Proxying block_unit_price_interactive/finalize request")
    try:
        body = await request.json()
        async with httpx.AsyncClient(timeout=60.0) as client:
            url = f"{LEDGER_API_BASE}/block_unit_price_interactive/finalize"
            logger.info(f"Forwarding to {url}")
            r = await client.post(url, json=body)
            logger.info(f"Ledger API response: {r.status_code}")
            r.raise_for_status()
            # BFF: ledger_apiの内部URLを外向きURLに変換
            response_data = r.json()
            return rewrite_artifact_urls_to_bff(response_data)
    except httpx.HTTPStatusError as e:
        logger.error(f"Ledger API error: {e.response.status_code}", exc_info=True)
        raise ExternalServiceError(
            service_name="ledger_api",
            message=f"Block unit price finalize failed: {str(e)}",
            status_code=e.response.status_code,
            cause=e
        )
    except httpx.HTTPError as e:
        logger.error(f"HTTP error: {str(e)}", exc_info=True)
        raise ExternalServiceError(
            service_name="ledger_api",
            message=f"Cannot reach ledger_api: {str(e)}",
            cause=e
        )
