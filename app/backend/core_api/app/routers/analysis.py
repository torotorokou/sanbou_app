"""
Analysis Router - BFF for analysis endpoints
フロントエンドからの分析リクエストを受け、適切なバックエンドサービスに転送
"""
import logging
import os
from fastapi import APIRouter, HTTPException, Request
import httpx

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["analysis"])

# ledger_api のベースURL（環境変数から取得、デフォルトはDocker Compose用）
LEDGER_API_BASE = os.getenv("LEDGER_API_BASE", "http://ledger_api:8002")


# TODO: 以下のエンドポイントは未実装（ledger_api側に実装が必要）
# @router.post("/customer-comparison/excel")
# async def proxy_customer_comparison_excel(request: Request):
#     """
#     顧客比較分析Excel出力（ledger_apiへフォワード）
#     """
#     logger.info("Proxying customer-comparison/excel request to ledger_api")
#     try:
#         body = await request.json()
#         async with httpx.AsyncClient(timeout=60.0) as client:
#             url = f"{LEDGER_API_BASE}/analysis/customer-comparison/excel"
#             r = await client.post(url, json=body)
#             r.raise_for_status()
#             # Excel blob を返す
#             return Response(content=r.content, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
#     except httpx.HTTPStatusError as e:
#         logger.error(f"Ledger API returned error: {e.response.status_code}")
#         raise HTTPException(
#             status_code=e.response.status_code,
#             detail={"code": "LEDGER_UPSTREAM_ERROR", "message": str(e)}
#         )
#     except httpx.HTTPError as e:
#         logger.error(f"Failed to reach ledger_api: {str(e)}")
#         raise HTTPException(
#             status_code=502,
#             detail={"code": "LEDGER_UNREACHABLE", "message": str(e)}
#         )
