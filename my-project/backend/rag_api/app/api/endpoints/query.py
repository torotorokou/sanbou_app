"""
FastAPIのエンドポイント定義。
AI回答生成やPDFページ画像取得、質問テンプレート取得APIを提供。

【フロントエンド開発者向けAPI説明】

■ 主要エンドポイント：

1. POST /test-answer (開発・テスト用)
   - 用途: フロントエンド開発時のモックAPI
   - レスポンス: ダミー回答 + 結合PDF URL
   - 処理時間: 高速（AI処理なし）

2. POST /generate-answer (本番用) 
   - 用途: 実際のAI回答生成
   - レスポンス: AI回答 + 結合PDF URL  
   - 処理時間: 数秒（AI処理あり）

■ 共通レスポンス形式：
{
  "status": "success",
  "code": "S200", 
  "detail": "処理成功メッセージ",
  "result": {
    "answer": "回答テキスト",
    "sources": [["PDF名", ページ番号], ...],
    "pdf_url": "結合PDFのダウンロードURL"
  }
}

■ PDFファイル管理：
- ユーザー用: /static/pdfs/merged_response_*.pdf
- 開発者用: /static/pdfs/debug/ (個別ページ)
- PDF URLは常に結合ファイルを指します

■ エラーレスポンス：
{
  "status": "error",
  "code": "E500",
  "detail": "エラー詳細", 
  "hint": "解決方法のヒント"
}
"""

import io
import os
import tempfile
import zipfile
from typing import Any, List, Tuple

import PyPDF2
from fastapi import APIRouter, Body, Request, Depends
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from app.core import file_ingest_service as loader
from app.infrastructure.pdf import pdf_loader
from app.schemas.query_schema import QueryRequest
from app.dependencies import get_dummy_response_service, get_ai_response_service
from backend_shared.src.api_response.response_base import SuccessApiResponse
from backend_shared.src.api_response.response_utils import api_response

router = APIRouter()

# --- Pydanticモデル ---


class QuestionRequest(BaseModel):
    query: str
    category: str
    tags: List[str]


class AnswerResponse(BaseModel):
    answer: str
    sources: List[Tuple[str, int]]


# --- generate-answer用レスポンスモデル ---


class QueryResponse(BaseModel):
    answer: str
    sources: Any
    pages: Any




# --- 質問を受け取ってダミー回答を返すAPI ---


@router.post("/test-answer", tags=["dummy"])
async def answer_api(
    req: QuestionRequest,
    dummy_service=Depends(get_dummy_response_service),
) -> dict:
    """
    【フロントエンド開発用】ダミーAI回答API
    
    フロントエンド開発時のモックAPIとして使用。
    AI処理を行わずに即座にダミーデータを返却するため、
    UI開発やテスト時に高速で動作確認が可能。
    
    リクエスト例:
    {
      "query": "売上を教えて",
      "category": "financial", 
      "tags": ["sales", "report"]
    }
    
    レスポンス:
    - answer: ダミー回答テキスト
    - sources: ダミー参照元（最大5つのPDFとページ番号）
    - pdf_url: 結合されたPDFのダウンロードURL
    
    注意: 本番環境では /generate-answer を使用すること
    """
    try:
        result = dummy_service.generate_dummy_response(req.query, req.category)
        return SuccessApiResponse(
            code="S200",
            detail="ダミーAI回答生成成功",
            result=result,
        ).to_json_response()
    except Exception as e:
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
) -> dict:
    """
    【本番用】AI回答生成API
    
    ユーザーからの質問に対してOpenAI GPTが実際に回答を生成。
    関連するPDFページを抽出・結合してダウンロード用URLを提供。
    
    リクエスト例:
    {
      "query": "今月の売上実績を教えて",
      "category": "financial",
      "tags": ["monthly", "sales"]
    }
    
    レスポンス:
    - answer: AIが生成した詳細回答
    - sources: 参照元PDFファイル名とページ番号のリスト
    - pdf_url: 関連ページを結合した1つのPDFのダウンロードURL
    
    処理時間: 通常2-5秒（AI処理とPDF生成を含む）
    
    フロントエンド実装時の注意:
    - ローディング表示を推奨（処理時間あり）
    - エラーハンドリングを実装すること
    - pdf_urlは直接<a>タグやwindow.openで使用可能
    """
    try:
        result = ai_service.generate_ai_response(request.query, request.category, request.tags)
        return SuccessApiResponse(
            code="S200",
            detail="AI回答生成成功",
            result=result,
        ).to_json_response()
    except Exception as e:
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
        from app.utils.file_utils import PDF_PATH

        pdf_path = str(PDF_PATH)
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
                reader = PyPDF2.PdfReader(f)
                writer = PyPDF2.PdfWriter()
                writer.add_page(reader.pages[page_num - 1])
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpf:
                    writer.write(tmpf)
                    tmpf.flush()
                    filename = tmpf.name
            headers = {"Content-Disposition": f"inline; filename=page_{page_num}.pdf"}
            return FileResponse(filename, media_type="application/pdf", headers=headers)

        # 複数ページの場合: ZIPで返却
        buf = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            with zipfile.ZipFile(buf, "w") as zipf:
                for p in pages:
                    try:
                        page_num = int(str(p).split("-")[0])
                    except Exception:
                        continue
                    writer = PyPDF2.PdfWriter()
                    writer.add_page(reader.pages[page_num - 1])
                    pdf_bytes = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                    writer.write(pdf_bytes)
                    pdf_bytes.flush()
                    pdf_bytes.seek(0)
                    zipf.write(pdf_bytes.name, arcname=f"page_{page_num}.pdf")
                    pdf_bytes.close()
                    os.unlink(pdf_bytes.name)
        buf.flush()
        headers = {"Content-Disposition": "attachment; filename=pages.zip"}
        return FileResponse(buf.name, media_type="application/zip", headers=headers)
    except Exception as e:
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
    from app.utils.file_utils import PDF_PATH

    pdf_path = str(PDF_PATH)
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


@router.get("/question-options", tags=["template"])
def get_question_options():
    """
    質問テンプレートをカテゴリ・タグごとにグループ化して返すエンドポイント。

    Returns:
        dict: カテゴリ・タグごとにグループ化されたテンプレート
    """
    data = loader.load_question_templates()

    # YAMLのカテゴリ:質問リスト形式をフラット化
    def flatten_templates(data):
        flat = []
        for category, questions in data[0].items():
            for q in questions:
                q = dict(q)  # copy
                q["category"] = category
                # tag→tagsにリネーム（OCP/既存関数互換）
                if "tag" in q:
                    q["tags"] = q.pop("tag")
                flat.append(q)
        return flat

    # データがカテゴリ:リスト形式ならフラット化
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        if all(isinstance(v, list) for v in data[0].values()):
            data = flatten_templates(data)

    grouped = loader.group_templates_by_category_and_tags(data)
    # tagsタプルを'|'区切りの文字列に変換
    grouped_strkey = {}
    for category, tags_dict in grouped.items():
        grouped_strkey[category] = {}
        for tags_tuple, titles in tags_dict.items():
            tags_str = "|".join(tags_tuple)
            grouped_strkey[category][tags_str] = titles
    return grouped_strkey
