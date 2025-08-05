"""
FastAPIのエンドポイント定義。
AI回答生成やPDFページ画像取得、質問テンプレート取得APIを提供。
"""
import random
from fastapi.responses import FileResponse
import re
import tempfile
import os
import io
import zipfile
from typing import List, Tuple
from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from app.schemas.query_schema import QueryRequest
from app.infrastructure.llm import ai_loader
from app.core import file_ingest_service as loader
from app.infrastructure.pdf import pdf_loader
from typing import Any
from fastapi import Request
import PyPDF2

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
@router.post("/test-answer")
async def answer_api(req: QuestionRequest):
    """
    ダミーAI回答・sources・pages・pdf_url/pdf_urlsを返すダミーAPI。
    - answer: ダミー回答
    - sources: ダミー参照元
    - pages: ランダムなページ番号または範囲
    - pdf_url/pdf_urls: SOLVEST.pdfのページを元に生成
    """
    # SOLVEST.pdfのパス（実際のPDFファイルを指定）
    # ダミーPDF保存先 statics/test_pdfs
    testpdf_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../statics/test_pdfs"))
    os.makedirs(testpdf_dir, exist_ok=True)
    pdf_path = os.path.join(testpdf_dir, "SOLVEST.pdf")
    # ページ数取得
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            total_pages = len(reader.pages)
    except Exception:
        total_pages = 10  # ファイルがなければ仮で10ページ

    # ランダムで1ページまたは複数ページを選択
    if random.random() < 0.5:
        # 単一ページ
        page = random.randint(1, total_pages)
        pages = [page]
    else:
        # 複数ページ
        start = random.randint(1, max(1, total_pages - 2))
        end = min(total_pages, start + random.randint(1, 3))
        pages = list(range(start, end + 1))

    # sourcesもダミー
    sources = [["SOLVEST.pdf", p] for p in pages]

    # safe_filenameでファイル名生成
    def safe_filename(s):
        return re.sub(r'[^A-Za-z0-9_-]', '', s)
    safe_name = safe_filename(req.query)

    # ダミーPDFをtest_pdfsに生成（なければ）
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for p in pages:
                dummy_pdf_path = os.path.join(testpdf_dir, f"answer_{safe_name}_{p}.pdf")
                if not os.path.exists(dummy_pdf_path):
                    writer = PyPDF2.PdfWriter()
                    # SOLVEST.pdfから該当ページを抜き出してPDFを作成
                    if 1 <= p <= len(reader.pages):
                        writer.add_page(reader.pages[p-1])
                    else:
                        # ページ範囲外なら空ページ
                        writer.add_blank_page(width=595, height=842)
                    with open(dummy_pdf_path, "wb") as out_f:
                        writer.write(out_f)
    except Exception:
        # SOLVEST.pdfが読めない場合は空PDF
        for p in pages:
            dummy_pdf_path = os.path.join(testpdf_dir, f"answer_{safe_name}_{p}.pdf")
            if not os.path.exists(dummy_pdf_path):
                writer = PyPDF2.PdfWriter()
                writer.add_blank_page(width=595, height=842)
                with open(dummy_pdf_path, "wb") as out_f:
                    writer.write(out_f)

    pdf_urls = [f"/test_pdfs/answer_{safe_name}_{p}.pdf" for p in pages]

    # ダミー回答
    answer = f"ダミー回答: {req.query}（カテゴリ: {req.category}）"

    # レスポンス形式をgenerate-answerと揃える
    if len(pdf_urls) == 1:
        return {"answer": answer, "sources": sources, "pdf_url": pdf_urls[0], "pages": pages}
    else:
        return {"answer": answer, "sources": sources, "pdf_urls": pdf_urls, "pages": pages}


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
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../static/pdfs"))
    os.makedirs(static_dir, exist_ok=True)
    print(f"[DEBUG] PDF保存先: {static_dir}")
    from app.utils.file_utils import PDF_PATH
    pdf_path = str(PDF_PATH)

    def safe_filename(s):
        # 英数字・アンダースコア・ハイフン以外は全て除去
        return re.sub(r'[^A-Za-z0-9_-]', '', s)

    pdf_urls = []
    if pages:
        # "177-178" のような範囲指定も分割してリスト化
        page_list = []
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
        else:
            page_list = []
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for p in page_list:
                try:
                    page_num = int(str(p).split("-")[0])
                except Exception:
                    continue
                writer = PyPDF2.PdfWriter()
                writer.add_page(reader.pages[page_num - 1])
                safe_name = safe_filename(request.query)
                filename = f"answer_{safe_name}_{page_num}.pdf"
                file_path = os.path.join(static_dir, filename)
                with open(file_path, "wb") as out_pdf:
                    writer.write(out_pdf)
                print(f"[DEBUG] PDF生成: {file_path}")
                # URLにもsafe_filenameを適用し、日本語・記号を含まないようにする
                pdf_urls.append(f"/pdfs/{filename}")

    # 単数ページならpdf_url、複数ならpdf_urls
    if len(pdf_urls) == 1:
        return {"answer": answer, "sources": sources, "pdf_url": pdf_urls[0]}
    elif len(pdf_urls) > 1:
        return {"answer": answer, "sources": sources, "pdf_urls": pdf_urls}
    else:
        return {"answer": answer, "sources": sources}

# --- PDF/ZIPファイルのみ返すAPI ---



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