"""
External router: proxies to internal microservices (rag_api, ledger_api, manual_api, ai_api).
For short synchronous calls only. Heavy jobs should be queued.
"""
from fastapi import APIRouter, HTTPException, Depends
import httpx
import logging

from app.config.di_providers import (
    get_ask_rag_uc,
    get_list_manuals_uc,
    get_get_manual_uc,
    get_generate_report_uc,
    get_classify_text_uc,
)
from app.application.usecases.external.external_api_uc import (
    AskRAGUseCase,
    ListManualsUseCase,
    GetManualUseCase,
    GenerateReportUseCase,
    ClassifyTextUseCase,
)
from app.presentation.schemas import RAGAskRequest, RAGAskResponse, ManualListResponse

router = APIRouter(prefix="/external", tags=["external"])
logger = logging.getLogger(__name__)


@router.post("/rag/ask", response_model=RAGAskResponse, summary="RAGに質問する")
async def ask_rag(
    req: RAGAskRequest,
    uc: AskRAGUseCase = Depends(get_ask_rag_uc),
):
    """
    RAG APIに質問を投げて回答を取得します。
    タイムアウト: 5秒（接続1秒、読み取り5秒）
    
    重い処理の場合はジョブキューに登録することを推奨します。
    """
    try:
        result = await uc.execute(req.query)
        return RAGAskResponse(
            answer=result.get("answer", ""),
            sources=result.get("sources"),
        )
    except httpx.TimeoutException:
        logger.error("RAG API タイムアウト", extra={"query": req.query})
        raise HTTPException(
            status_code=504,
            detail="RAG APIへの接続がタイムアウトしました。時間をおいて再度お試しください。"
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"RAG API エラー: {e.response.status_code}", extra={"query": req.query})
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"RAG APIでエラーが発生しました: {e.response.status_code}"
        )
    except Exception as e:
        logger.exception("RAG API 予期しないエラー", extra={"query": req.query})
        raise HTTPException(
            status_code=500,
            detail="RAG APIへの接続中に予期しないエラーが発生しました。"
        )


@router.get("/manual/list", response_model=ManualListResponse, summary="マニュアル一覧を取得")
async def list_manuals(
    uc: ListManualsUseCase = Depends(get_list_manuals_uc),
):
    """
    Manual APIからマニュアル一覧を取得します。
    
    重い処理の場合はジョブキューに登録することを推奨します。
    """
    try:
        manuals = await uc.execute()
        return ManualListResponse(manuals=manuals)
    except httpx.TimeoutException:
        logger.error("Manual API タイムアウト")
        raise HTTPException(
            status_code=504,
            detail="Manual APIへの接続がタイムアウトしました。"
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"Manual API エラー: {e.response.status_code}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Manual APIでエラーが発生しました: {e.response.status_code}"
        )
    except Exception as e:
        logger.exception("Manual API 予期しないエラー")
        raise HTTPException(
            status_code=500,
            detail="Manual APIへの接続中に予期しないエラーが発生しました。"
        )


@router.get("/manual/{manual_id}", summary="特定のマニュアルを取得")
async def get_manual(
    manual_id: str,
    uc: GetManualUseCase = Depends(get_get_manual_uc),
):
    """特定のマニュアルを ID で取得します。"""
    try:
        result = await uc.execute(manual_id)
        return result
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="マニュアルが見つかりません。")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Manual APIでエラーが発生しました: {e.response.status_code}"
        )
    except Exception as e:
        logger.exception("Manual API エラー", extra={"manual_id": manual_id})
        raise HTTPException(status_code=500, detail="マニュアル取得中にエラーが発生しました。")


@router.post("/ledger/reports/{report_type}", summary="帳票生成リクエスト")
async def generate_report(
    report_type: str,
    params: dict,
    uc: GenerateReportUseCase = Depends(get_generate_report_uc),
):
    """
    Ledger APIに帳票生成をリクエストします。
    
    重い処理の場合はジョブキューに登録することを推奨します（TODO）。
    """
    try:
        result = await uc.execute(report_type, params)
        return result
    except httpx.TimeoutException:
        logger.error("Ledger API タイムアウト", extra={"report_type": report_type})
        raise HTTPException(
            status_code=504,
            detail="Ledger APIへの接続がタイムアウトしました。"
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"Ledger API エラー: {e.response.status_code}", extra={"report_type": report_type})
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Ledger APIでエラーが発生しました: {e.response.status_code}"
        )
    except Exception as e:
        logger.exception("Ledger API エラー", extra={"report_type": report_type})
        raise HTTPException(status_code=500, detail="帳票生成中にエラーが発生しました。")


@router.post("/ai/classify", summary="テキスト分類")
async def classify_text(
    text: str,
    uc: ClassifyTextUseCase = Depends(get_classify_text_uc),
):
    """AI APIを使ってテキストを分類します。"""
    try:
        result = await uc.execute(text)
        return result
    except httpx.TimeoutException:
        logger.error("AI API タイムアウト")
        raise HTTPException(status_code=504, detail="AI APIへの接続がタイムアウトしました。")
    except httpx.HTTPStatusError as e:
        logger.error(f"AI API エラー: {e.response.status_code}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"AI APIでエラーが発生しました: {e.response.status_code}"
        )
    except Exception as e:
        logger.exception("AI API エラー")
        raise HTTPException(status_code=500, detail="テキスト分類中にエラーが発生しました。")
