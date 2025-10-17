"""
Chat Router - BFF for rag_api chat endpoints
フロントエンドからのチャットリクエストを受け、rag_apiに転送
"""
import logging
import os
from fastapi import APIRouter, HTTPException, Request
import httpx

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["rag"])

# rag_api のベースURL（環境変数から取得、デフォルトはDocker Compose用）
RAG_API_BASE = os.getenv("RAG_API_BASE", "http://rag_api:8003")


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
        raise HTTPException(
            status_code=e.response.status_code,
            detail={
                "code": "RAG_UPSTREAM_ERROR",
                "message": f"RAG API error: {e.response.text[:200]}"
            }
        )
    except httpx.HTTPError as e:
        logger.error(f"Failed to reach rag_api: {str(e)}")
        raise HTTPException(
            status_code=502,
            detail={
                "code": "RAG_UNREACHABLE",
                "message": f"Cannot reach rag_api: {str(e)}"
            }
        )


@router.post("/generate-answer")
async def proxy_generate_answer(request: Request):
    """
    AI回答を生成（rag_apiへフォワード）
    """
    logger.info("Proxying POST /rag/generate-answer to rag_api")
    try:
        body = await request.json()
        async with httpx.AsyncClient(timeout=60.0) as client:
            url = f"{RAG_API_BASE}/api/generate-answer"
            r = await client.post(url, json=body)
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"RAG API returned error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail={
                "code": "RAG_UPSTREAM_ERROR",
                "message": f"RAG API error: {e.response.text[:200]}"
            }
        )
    except httpx.HTTPError as e:
        logger.error(f"Failed to reach rag_api: {str(e)}")
        raise HTTPException(
            status_code=502,
            detail={
                "code": "RAG_UNREACHABLE",
                "message": f"Cannot reach rag_api: {str(e)}"
            }
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
        raise HTTPException(
            status_code=e.response.status_code,
            detail={
                "code": "RAG_UPSTREAM_ERROR",
                "message": f"RAG API error: {e.response.text[:200]}"
            }
        )
    except httpx.HTTPError as e:
        logger.error(f"Failed to reach rag_api: {str(e)}")
        raise HTTPException(
            status_code=502,
            detail={
                "code": "RAG_UNREACHABLE",
                "message": f"Cannot reach rag_api: {str(e)}"
            }
        )
