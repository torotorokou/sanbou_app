"""
FastAPIのエンドポイント定義。
AI回答生成やPDFページ画像取得、質問テンプレート取得APIを提供。
"""

import io
import os
import re
import tempfile
import zipfile
from typing import Any, List, Tuple

import PyPDF2
from fastapi import APIRouter, Body, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

from app.core import file_ingest_service as loader
from app.infrastructure.llm import ai_loader
from app.infrastructure.pdf import pdf_loader
from app.schemas.query_schema import QueryRequest

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


def save_pdf_pages_and_get_urls(pdf_path, query_name, pages, save_dir, url_prefix):
    """
    指定PDFからpagesの各ページを抽出し、save_dirにanswer_{query_name}_{p}.pdfで保存。
    既存ならスキップ。URLリストを返す。
    """
    def safe_filename(s):
        return re.sub(r'[^A-Za-z0-9_-]', '', s)
    safe_name = safe_filename(query_name)
    os.makedirs(save_dir, exist_ok=True)
    pdf_urls = []
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for p in pages:
                dummy_pdf_path = os.path.join(save_dir, f"answer_{safe_name}_{p}.pdf")
                if not os.path.exists(dummy_pdf_path):
                    writer = PyPDF2.PdfWriter()
                    if 1 <= p <= len(reader.pages):
                        writer.add_page(reader.pages[p-1])
                    else:
                        writer.add_blank_page(width=595, height=842)
                    with open(dummy_pdf_path, "wb") as out_f:
                        writer.write(out_f)
                pdf_urls.append(f"{url_prefix}/answer_{safe_name}_{p}.pdf")
    except Exception:
        # PDF読めない場合は空PDF
        for p in pages:
            dummy_pdf_path = os.path.join(save_dir, f"answer_{safe_name}_{p}.pdf")
            if not os.path.exists(dummy_pdf_path):
                writer = PyPDF2.PdfWriter()
                writer.add_blank_page(width=595, height=842)
                with open(dummy_pdf_path, "wb") as out_f:
                    writer.write(out_f)
            pdf_urls.append(f"{url_prefix}/answer_{safe_name}_{p}.pdf")
    return pdf_urls

# --- 質問を受け取ってダミー回答を返すAPI ---

@router.post("/test-answer")
async def answer_api(req: QuestionRequest):
    """
    ダミーAI回答・sources・pages・pdf_urls・merged_pdf_urlを返すダミーAPI。
    - answer: ダミー回答
    - sources: ダミー参照元（pdfs/の先頭5ファイル）
    - pages: [3,4,5,6,7]（固定）
    - pdf_urls: pdfs/の先頭5ファイルのURL
    - merged_pdf_url: 5つのPDFを結合した1つのPDFのURL
    """
    # PDF保存先（本番と同じディレクトリを参照）
    pdfs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../static/pdfs"))
    os.makedirs(pdfs_dir, exist_ok=True)
    # pdfs/ディレクトリ内のPDFファイル一覧（先頭5つ取得）
    pdf_files = [f for f in os.listdir(pdfs_dir) if f.lower().endswith(".pdf")]
    pdf_files.sort()  # ファイル名順
    selected_files = pdf_files[:5]
    # ページ番号は3,4,5,6,7で固定（ファイル数が足りなければ補完）
    pages = list(range(3, 8))[:len(selected_files)]
    sources = [[selected_files[i] if i < len(selected_files) else "dummy.pdf", pages[i]] for i in range(len(pages))]
    # pdf_urls生成
    pdf_urls = [f"/pdfs/{selected_files[i]}" for i in range(len(selected_files))]

    # 5つのPDFを結合して1つのPDFを生成
    merged_pdf_name = f"merged_{req.query}.pdf"
    merged_pdf_path = os.path.join(pdfs_dir, merged_pdf_name)
    writer = PyPDF2.PdfWriter()
    for fname in selected_files:
        fpath = os.path.join(pdfs_dir, fname)
        try:
            with open(fpath, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    writer.add_page(page)
        except Exception:
            # ファイル読めない場合は空ページ
            writer.add_blank_page(width=595, height=842)
    with open(merged_pdf_path, "wb") as out_f:
        writer.write(out_f)
    merged_pdf_url = f"/pdfs/{merged_pdf_name}"

    # ダミー回答
    answer = f"ダミー回答: {req.query}（カテゴリ: {req.category}）"

    return {
        "answer": answer,
        "sources": sources,
        "pdf_urls": pdf_urls,
        "pages": pages,
        "merged_pdf_url": merged_pdf_url
    }


# --- AI回答＋PDF URL返却API ---
@router.post("/generate-answer")
async def generate_answer(request: QueryRequest):
    """
    ユーザーからの質問に対してAIが回答を生成し、回答・参照元・PDFのURLを返すAPI。

    【フロントエンジニア向け説明】
    - レスポンスはJSON形式で、AI回答（answer）、参照元（sources）、およびPDFファイルのURL（pdf_url または pdf_urls）を返します。
    - PDFはサーバーの static/pdfs ディレクトリに保存され、URLは `/rag_api/pdfs/ファイル名.pdf` 形式で直接アクセス可能です。
    - ファイル名・URLには日本語や記号は含まれず、英数字・アンダースコア・ハイフンのみとなります。
    - 複数ページの場合は "pdf_urls"（リスト）、単一ページの場合は "pdf_url"（文字列）で返却されます。
    - 例：
        {
            "answer": "...AIの回答...",
            "sources": [...],
            "pdf_url": "/pdfs/answer_query_286.pdf"
        }
        または
        {
            "answer": "...AIの回答...",
            "sources": [...],
            "pdf_urls": ["/pdfs/answer_query_286.pdf", "/pdfs/answer_query_287.pdf"]
        }
    - 返却されたURLはそのままiframeやaタグ、window.open等でWeb表示・ダウンロードに利用できます。
    - 注意：URLの先頭に `/rag_api` が付与されていることを確認してください（例：`http://localhost:8004/rag_api/pdfs/answer_query_286.pdf`）。
    """
    result = ai_loader.get_answer(request.query, request.category, request.tags)
    answer = result["answer"]
    sources = result["sources"]
    pages = result["pages"]

    # PDF保存先ディレクトリ
    # FastAPIの公開ディレクトリと一致しているか確認用ログ
    # main.pyの公開ディレクトリと必ず一致させる
    static_dir = os.environ.get("PDFS_DIR") or "/backend/static/pdfs"
    os.makedirs(static_dir, exist_ok=True)
    print(f"[DEBUG] PDF保存先: {static_dir}")
    from app.utils.file_utils import PDF_PATH
    pdf_path = str(PDF_PATH)

    # ページリストを正規化
    page_list = []
    if pages:
        if isinstance(pages, str):
            if '-' in pages:
                start, end = pages.split('-')
                try:
                    start = int(start)
                    end = int(end)
                    page_list = list(range(start, end + 1))
                except Exception:
                    page_list = [pages]
            else:
                page_list = [pages]
        elif isinstance(pages, list):
            for p in pages:
                if isinstance(p, str) and '-' in p:
                    try:
                        start, end = p.split('-')
                        start = int(start)
                        end = int(end)
                        page_list.extend(range(start, end + 1))
                    except Exception:
                        page_list.append(p)
                else:
                    page_list.append(p)

    # 共通関数でPDF保存＆URL生成
    pdf_urls = save_pdf_pages_and_get_urls(
        pdf_path=pdf_path,
        query_name=request.query,
        pages=page_list,
        save_dir=static_dir,
        url_prefix="/pdfs"
    )

    # 個別PDFを結合した1つのPDFも生成
    merged_pdf_name = f"merged_{request.query}.pdf"
    merged_pdf_path = os.path.join(static_dir, merged_pdf_name)
    writer = PyPDF2.PdfWriter()
    for url in pdf_urls:
        fname = url.split("/")[-1]
        fpath = os.path.join(static_dir, fname)
        try:
            with open(fpath, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    writer.add_page(page)
        except Exception:
            writer.add_blank_page(width=595, height=842)
    with open(merged_pdf_path, "wb") as out_f:
        writer.write(out_f)
    merged_pdf_url = f"/pdfs/{merged_pdf_name}"

    # 単数ページならpdf_url、複数ならpdf_urls
    if len(pdf_urls) == 1:
        return {
            "answer": answer,
            "sources": sources,
            "pdf_url": pdf_urls[0],
            "pdf_urls": pdf_urls,
            "merged_pdf_url": merged_pdf_url
        }
    elif len(pdf_urls) > 1:
        return {
            "answer": answer,
            "sources": sources,
            "pdf_urls": pdf_urls,
            "merged_pdf_url": merged_pdf_url
        }
    else:
        return {
            "answer": answer,
            "sources": sources,
            "merged_pdf_url": merged_pdf_url
        }





@router.post("/download-report")
async def download_report(request: Request, pages: list = Body(..., embed=True)):
    """
    指定されたページリストに基づき、単数ページならPDF、複数ページならZIPで返却。
    pages: [1] または [1,2,3] のようなリスト
    """
    from app.utils.file_utils import PDF_PATH
    pdf_path = str(PDF_PATH)
    if not pages or not isinstance(pages, list):
        return JSONResponse(status_code=422, content={"detail": "pagesはリストで指定してください。"})

    # 単数ページの場合: PDFで返却
    if len(pages) == 1:
        try:
            page_num = int(str(pages[0]).split("-")[0])
        except Exception:
            return JSONResponse(status_code=400, content={"detail": "ページ番号が不正です。"})
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

# --- PDFページ画像返却API ---
@router.get("/pdf-page")
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


@router.get("/question-options")
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