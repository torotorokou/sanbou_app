"""
FastAPIのエンドポイント定義。
AI回答生成やPDFページ画像取得、質問テンプレート取得APIを提供。
"""

import io
import os
import tempfile
import zipfile
from typing import Any, List, Tuple

import pypdf
from fastapi import APIRouter, Body, Request, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel

from backend_shared.application.logging import get_module_logger
from app.core.usecases.rag import file_ingest_service as loader
from app.infra.adapters.pdf import pdf_loader
from app.api.schemas.query_schema import QueryRequest, QueryResponse
from app.api.dependencies import get_dummy_response_service, get_ai_response_service
from backend_shared.infra.adapters.presentation.response_base import SuccessApiResponse, ErrorApiResponse
from backend_shared.infra.adapters.presentation.response_utils import api_response

logger = get_module_logger(__name__)
router = APIRouter()

# --- 質問を受け取ってダミー回答を返すAPI ---


@router.post("/test-answer", tags=["dummy"])
async def answer_api(
    req: QueryRequest,
    dummy_service=Depends(get_dummy_response_service),
) -> JSONResponse:
    try:
        logger.debug("Test answer request", extra={"request": req.dict()})
        result = dummy_service.generate_dummy_response(req.query, req.category)
        logger.debug("Test answer result", extra={"result_keys": list(result.keys())})
        return SuccessApiResponse(
            code="S200",
            detail="ダミーAI回答生成成功",
            result=result,
        ).to_json_response()
    except Exception as e:
        logger.error("Test answer exception", extra={"error": repr(e)}, exc_info=True)
        return api_response(
            status_code=500,
            status_str="error",
            code="E500",
            detail=f"Internal Server Error: {str(e)}",
            hint="サーバー側で予期せぬエラーが発生しました。管理者に連絡してください。",
        )


# --- AI回答＋PDF URL返却API ---
@router.post("/generate-answer", tags=["ai"])
async def generate_answer(
    request: QueryRequest,
    ai_service=Depends(get_ai_response_service),
) -> JSONResponse:
    logger.info("Generate answer request", extra={"query": request.query, "category": request.category, "tags": request.tags})
    try:
        logger.debug(
            "Generate answer request details",
            extra={
                "query": request.query,
                "category": request.category,
                "tags": request.tags
            }
        )
        result = ai_service.generate_ai_response(request.query, request.category, request.tags)
        logger.debug("Generate answer result", extra={"result_keys": list(result.keys())})
        
        # エラーコードの存在をチェック
        if "error_code" in result:
            error_code = result.get("error_code", "OPENAI_ERROR")
            error_detail = result.get("error_detail", "AI回答の生成に失敗しました。")
            logger.error("Generate answer failed", extra={"error_code": error_code, "error_detail": error_detail})
            logger.debug("Error detected in result", extra={"error_code": error_code})
            
            # エラーコードに応じたヒントメッセージ
            if error_code == "OPENAI_INSUFFICIENT_QUOTA":
                hint = "OpenAI APIの利用上限を超過しています。システム管理者にお問い合わせください。"
            elif error_code == "OPENAI_RATE_LIMIT":
                hint = "一時的なレート制限です。しばらく時間をおいて再度お試しください。"
            else:
                hint = "エラーが継続する場合は管理者にお問い合わせください。"
            
            return ErrorApiResponse(
                code=error_code,
                detail=error_detail,
                hint=hint,
                status_code=200,  # 既存互換性のため200を維持
            ).to_json_response()
        
        # 正常系の処理
        logger.debug(
            "Generate answer success details",
            extra={
                "pdf_url": result.get("pdf_url"),
                "sources_count": len(result.get("sources", []))
            }
        )

        answer_ok = bool(result.get("answer"))
        pdf_ok = bool(result.get("pdf_url"))

        if answer_ok and pdf_ok:
            # 両方成功
            logger.info("Generate answer succeeded", extra={"answer_length": len(result.get("answer", "")), "has_pdf": True})
            return SuccessApiResponse(
                code="S200",
                detail="AI回答生成成功",
                result=result,
            ).to_json_response()
        if answer_ok and not pdf_ok:
            # 回答は成功、PDFは失敗
            logger.warning("Generate answer succeeded without PDF", extra={"answer_length": len(result.get("answer", ""))})
            return SuccessApiResponse(
                code="S200",
                detail="AI回答生成（PDFなし）",
                hint="関連するPDFが見つからなかった、または生成に失敗したため、PDFは参照できません。回答のみ返却します。",
                result=result,
            ).to_json_response()
        # answer失敗（空/None）
        logger.error("Generate answer failed - no answer generated")
        return ErrorApiResponse(
            code="E400",
            detail="回答生成に失敗しました。",
            hint="質問内容やタグを見直して再度お試しください。改善しない場合は管理者に連絡してください。",
            result=None,
            status_code=200,
        ).to_json_response()
    except ValueError as e:
        # 予期したValueErrorはanswerが空のケースとして扱い、ErrorApiResponse
        logger.error("Generate answer ValueError", exc_info=True, extra={"error": str(e)})
        return ErrorApiResponse(
            code="E400",
            detail="回答生成に失敗しました。",
            hint="質問内容やタグを見直して再度お試しください。改善しない場合は管理者に連絡してください。",
            result=None,
            status_code=500,
        ).to_json_response()
    except Exception as e:
        logger.error("Generate answer exception", exc_info=True, extra={"error": str(e)})
        return api_response(
            status_code=500,
            status_str="error",
            code="E500",
            detail=f"Internal Server Error: {str(e)}",
            hint="サーバー側で予期せぬエラーが発生しました。管理者に連絡してください。",
        )


@router.post("/download-report", tags=["pdf"])
async def download_report(request: Request, pages: list = Body(..., embed=True)):
    """
    指定されたページリストに基づき、単数ページならPDF、複数ページならZIPで返却。
    pages: [1] または [1,2,3] のようなリスト
    """
    try:
        from app.shared.file_utils import PDF_PATH

        pdf_path = str(PDF_PATH)
        logger.debug(
            "Download report request",
            extra={"pages": pages, "pdf_path": pdf_path}
        )
        if not pages or not isinstance(pages, list):
            return api_response(
                status_code=422,
                status_str="error",
                code="E422",
                detail="pagesはリストで指定してください。",
                hint="リクエストボディのpagesをリスト形式で指定してください。",
            )

        # 単数ページの場合: PDFで返却
        if len(pages) == 1:
            try:
                page_num = int(str(pages[0]).split("-")[0])
            except Exception:
                return api_response(
                    status_code=400,
                    status_str="error",
                    code="E400",
                    detail="ページ番号が不正です。",
                    hint="pagesの値を確認してください。",
                )
            with open(pdf_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                writer = pypdf.PdfWriter()
                writer.add_page(reader.pages[page_num - 1])
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpf:
                    writer.write(tmpf)
                    tmpf.flush()
                    filename = tmpf.name
            logger.debug("Single page generated", extra={"filename": filename})
            headers = {"Content-Disposition": f"inline; filename=page_{page_num}.pdf"}
            return FileResponse(filename, media_type="application/pdf", headers=headers)

        # 複数ページの場合: ZIPで返却
        buf = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
        with open(pdf_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            with zipfile.ZipFile(buf, "w") as zipf:
                for p in pages:
                    try:
                        page_num = int(str(p).split("-")[0])
                    except Exception:
                        continue
                    writer = pypdf.PdfWriter()
                    writer.add_page(reader.pages[page_num - 1])
                    pdf_bytes = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                    writer.write(pdf_bytes)
                    pdf_bytes.flush()
                    pdf_bytes.seek(0)
                    zipf.write(pdf_bytes.name, arcname=f"page_{page_num}.pdf")
                    pdf_bytes.close()
                    os.unlink(pdf_bytes.name)
        buf.flush()
        logger.debug("ZIP generated", extra={"zip_path": buf.name})
        headers = {"Content-Disposition": "attachment; filename=pages.zip"}
        return FileResponse(buf.name, media_type="application/zip", headers=headers)
    except Exception as e:
        logger.error("Download report exception", extra={"error": repr(e)}, exc_info=True)
        return api_response(
            status_code=500,
            status_str="error",
            code="E500",
            detail=f"Internal Server Error: {str(e)}",
            hint="サーバー側で予期せぬエラーが発生しました。管理者に連絡してください。",
        )


# --- PDFページ画像返却API ---
@router.get("/pdf-page", tags=["pdf"])
def pdf_page(page_num: str):
    """
    指定されたPDFページ番号の画像を返すエンドポイント。
    1ページの場合はPNG画像、範囲指定（例: 1-3）の場合はZIPで複数ページを返す。
    """
    from app.shared.file_utils import PDF_PATH

    pdf_path = str(PDF_PATH)
    logger.debug(
        "PDF page request",
        extra={"page_num": page_num, "pdf_path": pdf_path}
    )
    if "-" in page_num:
        start, end = page_num.split("-")
        start = int(start)
        end = int(end)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zipf:
            for p in range(start, end + 1):
                img_bytes = pdf_loader.get_pdf_page_image(pdf_path, p)
                zipf.writestr(f"page_{p}.png", img_bytes.getvalue())
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=pages.zip"},
        )
    else:
        p = int(page_num)
        image_bytes = pdf_loader.get_pdf_page_image(pdf_path, p)
        return StreamingResponse(image_bytes, media_type="image/png")


@router.get("/question-options", tags=["question"])
def get_question_options():
    """
    質問テンプレートをカテゴリ・タグごとにグループ化して返すエンドポイント。

    Returns:
        dict: YAMLファイルと同じ、カテゴリ名 => [ { title, tag }, ... ] 構造
    """
    data = loader.load_question_templates()
    # すでに YAML と同等の {カテゴリ: [ {title, tag}, ... ]} 構造で
    # 読み込めている場合（load_question_templates は dict を [dict] で返す）
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return data[0]

    # フラット（{category, title, tags|tag}）な形式から YAML と同じ構造を再構築
    nested = {}
    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            category = item.get("category")
            title = item.get("title")
            tags = item.get("tag")
            if tags is None:
                tags = item.get("tags", [])

            if not category or not title:
                continue

            def _append(cat):
                nested.setdefault(cat, []).append({"title": title, "tag": tags})

            if isinstance(category, list):
                for cat in category:
                    _append(cat)
            else:
                _append(category)

    return nested


# --- 環境デバッグ（キー存在確認・マスク表示） ---
@router.get("/debug-keys", tags=["debug"])
def debug_keys() -> JSONResponse:
    """
    デバッグ用エンドポイント（開発環境のみ）
    本番環境・ステージング環境では無効化されます。
    """
    import os
    stage = os.environ.get("STAGE", "").lower()
    
    # 本番・ステージング環境では404を返す
    if stage in ("prod", "stg"):
        raise HTTPException(
            status_code=404,
            detail="Not found"
        )
    
    k = os.environ.get("OPENAI_API_KEY")
    masked = f"***{k[-4:]}" if k and len(k) > 8 else ("set" if k else "missing")
    payload = {
        "OPENAI_API_KEY": masked,
        "SECRETS_LOADED_FROM": os.environ.get("SECRETS_LOADED_FROM"),
        "STAGE": os.environ.get("STAGE"),
    }
    return SuccessApiResponse(
        code="S200",
        detail="env debug",
        result=payload,
    ).to_json_response()
