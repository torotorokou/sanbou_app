"""
Database Router - BFF for database/sql_api endpoints
フロントエンドからのデータベース操作リクエストを受け、sql_apiに転送
"""
import logging
import os
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
import httpx

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/database", tags=["database"])

# sql_api のベースURL（環境変数から取得、デフォルトはDocker Compose用）
SQL_API_BASE = os.getenv("SQL_API_BASE", "http://sql_api:8001")


# TODO: 以下のエンドポイントは未実装（sql_api側に実装が必要）
# @router.post("/upload/syogun_csv")
# async def proxy_syogun_csv_upload(file: UploadFile = File(...)):
#     """
#     正群CSVアップロード（sql_apiへフォワード）
#     """
#     logger.info("Proxying database/upload/syogun_csv request to sql_api")
#     try:
#         # FormData を受け取って sql_api へフォワード
#         form_data = FormData()
#         form_data.add_field('file', await file.read(), filename=file.filename, content_type=file.content_type)
#         
#         async with httpx.AsyncClient(timeout=60.0) as client:
#             url = f"{SQL_API_BASE}/upload/syogun_csv"
#             r = await client.post(url, data=form_data)
#             r.raise_for_status()
#             return r.json()
#     except httpx.HTTPStatusError as e:
#         logger.error(f"SQL API returned error: {e.response.status_code}")
#         raise HTTPException(
#             status_code=e.response.status_code,
#             detail={"code": "SQL_UPSTREAM_ERROR", "message": str(e)}
#         )
#     except httpx.HTTPError as e:
#         logger.error(f"Failed to reach sql_api: {str(e)}")
#         raise HTTPException(
#             status_code=502,
#             detail={"code": "SQL_UNREACHABLE", "message": str(e)}
#         )
