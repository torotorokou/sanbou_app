"""
Factory Report - 工場日報生成エンドポイント
"""
import logging
import os
from fastapi import APIRouter, Request
import httpx

from app.shared.exceptions import ExternalServiceError
from app.shared.utils import rewrite_artifact_urls_to_bff

logger = logging.getLogger(__name__)

router = APIRouter()

LEDGER_API_BASE = os.getenv("LEDGER_API_BASE", "http://ledger_api:8000")


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
