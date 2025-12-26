"""
Chat Router - BFF for rag_api chat endpoints
フロントエンドからのチャットリクエストを受け、rag_apiに転送

設計方針:
  - カスタム例外を使用(HTTPExceptionは使用しない)
  - ExternalServiceError で外部サービスエラーをラップ
"""

import os

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import Response

from backend_shared.application.logging import get_module_logger
from backend_shared.core.domain.exceptions import ExternalServiceError

logger = get_module_logger(__name__)

router = APIRouter(prefix="/rag", tags=["rag"])

# rag_api のベースURL（環境変数から取得、デフォルトはDocker Compose用）
RAG_API_BASE = os.getenv("RAG_API_BASE", "http://rag_api:8000")


@router.get("/question-options")
async def proxy_question_options():
    """
    質問テンプレート一覧を取得（rag_apiへフォワード）
    """
    logger.info("Proxying GET /rag/question-options to rag_api")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{RAG_API_BASE}/api/question-options"
            r = await client.get(url)
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"RAG API returned error: {e.response.status_code} - {e.response.text}")
        raise ExternalServiceError(
            service_name="rag_api",
            message=f"Question options fetch failed: {e.response.text[:200]}",
            status_code=e.response.status_code,
            cause=e,
        )
    except httpx.HTTPError as e:
        logger.error(f"Failed to reach rag_api: {str(e)}")
        raise ExternalServiceError(
            service_name="rag_api", message=f"Cannot reach rag_api: {str(e)}", cause=e
        )


@router.post("/generate-answer")
async def proxy_generate_answer(request: Request):
    """
    AI回答を生成（rag_apiへフォワード）
    フロントエンド互換のため、レスポンスを変換する
    """
    logger.info("Proxying POST /rag/generate-answer to rag_api")
    try:
        body = await request.json()
        async with httpx.AsyncClient(timeout=60.0) as client:
            url = f"{RAG_API_BASE}/api/generate-answer"
            r = await client.post(url, json=body)
            r.raise_for_status()
            rag_response = r.json()

            # rag_apiのレスポンス構造をログ出力
            logger.info(f"RAG API response keys: {list(rag_response.keys())}")

            # SuccessApiResponse形式の場合、resultフィールドを展開
            if "result" in rag_response and rag_response.get("status") == "success":
                result_data = rag_response["result"]
                logger.info(f"Extracting from result field. Keys: {list(result_data.keys())}")

                # PDF URLをcore_api経由のURLに変換
                pdf_url = result_data.get("pdf_url")
                if pdf_url and pdf_url.startswith("/rag_api/pdfs/"):
                    # /rag_api/pdfs/xxx.pdf -> /core_api/rag/pdfs/xxx.pdf
                    pdf_url = pdf_url.replace("/rag_api/pdfs/", "/core_api/rag/pdfs/")
                    logger.info(f"Converted PDF URL: {pdf_url}")

                return {
                    "answer": result_data.get("answer", ""),
                    "pdf_url": pdf_url,
                    "sources": result_data.get("sources", []),
                }

            # エラーレスポンスの場合、status/code/detailをそのまま返す
            if rag_response.get("status") == "error":
                logger.warning(
                    f"RAG API returned error: code={rag_response.get('code')}, detail={rag_response.get('detail')}"
                )
                return {
                    "status": "error",
                    "code": rag_response.get("code", "UNKNOWN_ERROR"),
                    "detail": rag_response.get("detail", "エラーが発生しました"),
                    "hint": rag_response.get("hint"),
                }

            # 既に期待される形式の場合はそのまま返す
            return rag_response
    except httpx.HTTPStatusError as e:
        logger.error(f"RAG API returned error: {e.response.status_code} - {e.response.text}")
        raise ExternalServiceError(
            service_name="rag_api",
            message=f"Answer generation failed: {e.response.text[:200]}",
            status_code=e.response.status_code,
            cause=e,
        )
    except httpx.HTTPError as e:
        logger.error(f"Failed to reach rag_api: {str(e)}")
        raise ExternalServiceError(
            service_name="rag_api", message=f"Cannot reach rag_api: {str(e)}", cause=e
        )


@router.get("/pdfs/{file_path:path}")
async def proxy_pdf(file_path: str):
    """
    PDFファイルをrag_apiからプロキシ配信
    /core_api/rag/pdfs/xxx.pdf -> rag_api:/rag_api/pdfs/xxx.pdf
    (rag_apiのroot_pathが/rag_apiのため)
    """
    logger.info(f"Proxying PDF request: {file_path}")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # rag_apiはroot_path="/rag_api"なので、/rag_api/pdfs/...でアクセス
            url = f"{RAG_API_BASE}/rag_api/pdfs/{file_path}"
            logger.info(f"Fetching PDF from: {url}")
            r = await client.get(url)
            r.raise_for_status()

            # PDFのContent-Typeとバイナリデータをそのまま返す
            return Response(
                content=r.content,
                media_type=r.headers.get("content-type", "application/pdf"),
                headers={
                    "Content-Disposition": r.headers.get(
                        "content-disposition",
                        f"inline; filename={file_path.split('/')[-1]}",
                    )
                },
            )
    except httpx.HTTPStatusError as e:
        logger.error(f"RAG API PDF error: {e.response.status_code} - {file_path}")
        raise ExternalServiceError(
            service_name="rag_api",
            message=f"PDF file not found: {file_path}",
            status_code=e.response.status_code,
            cause=e,
        )
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch PDF from rag_api: {str(e)}")
        raise ExternalServiceError(
            service_name="rag_api", message=f"Cannot fetch PDF: {str(e)}", cause=e
        )


@router.post("/test-answer")
async def proxy_test_answer(request: Request):
    """
    テスト回答生成（rag_apiへフォワード）
    """
    logger.info("Proxying chat/test-answer request to rag_api")
    try:
        body = await request.json()
        async with httpx.AsyncClient(timeout=60.0) as client:
            url = f"{RAG_API_BASE}/test-answer"
            r = await client.post(url, json=body)
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"RAG API returned error: {e.response.status_code} - {e.response.text}")
        raise ExternalServiceError(
            service_name="rag_api",
            message=f"Test answer generation failed: {e.response.text[:200]}",
            status_code=e.response.status_code,
            cause=e,
        )
    except httpx.HTTPError as e:
        logger.error(f"Failed to reach rag_api: {str(e)}")
        raise ExternalServiceError(
            service_name="rag_api", message=f"Cannot reach rag_api: {str(e)}", cause=e
        )
