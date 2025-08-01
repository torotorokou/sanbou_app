from fastapi import APIRouter
"""
FastAPIのエンドポイント定義。
AI回答生成やPDFページ画像取得、質問テンプレート取得APIを提供。
"""

from fastapi.responses import StreamingResponse
from app.schemas.query_schema import QueryRequest, QueryResponse
from app.infrastructure.llm import ai_loader
from app.core import file_ingest_service as loader
from app.infrastructure.pdf import pdf_loader

import io

import zipfile

router = APIRouter()



@router.post("/generate-answer", response_model=QueryResponse)
async def generate_answer(request: QueryRequest):
    """
    ユーザーからの質問に対してAIが回答を生成し、回答・参照元・ページ情報を返すエンドポイント。
    """
    ユーザーからの質問に対してAIが回答を生成し、回答・参照元・ページ情報を返すエンドポイント。

    Args:
        request (QueryRequest): クエリ、カテゴリ、タグを含むリクエストボディ
    Returns:
        QueryResponse: 回答、参照元、ページ情報
    """
    return QueryResponse(answer=result["answer"], sources=result["sources"], pages=result["pages"])

@router.get("/pdf-page")
    return QueryResponse(answer=result["answer"], sources=result["sources"], pages=result["pages"])
    """
    指定されたPDFページ番号の画像を返すエンドポイント。
    """
    指定されたPDFページ番号の画像を返すエンドポイント。
    1ページの場合はPNG画像、範囲指定（例: 1-3）の場合はZIPで複数ページを返す。

    Args:
        page_num (str): ページ番号または範囲（例: '1' または '1-3'）
    Returns:
        StreamingResponse: 画像またはZIPファイルのストリーミングレスポンス
    """

    if '-' in page_num:
        # ページ範囲指定の場合、各ページ画像をZIPにまとめて返す
        start, end = page_num.split('-')
        start = int(start)
        end = int(end)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zipf:
            for p in range(start, end + 1):
                img_bytes = pdf_loader.get_pdf_page_image(pdf_path, p)
                zipf.writestr(f'page_{p}.png', img_bytes.getvalue())
        buf.seek(0)
        return StreamingResponse(buf, media_type="application/zip", headers={"Content-Disposition": "attachment; filename=pages.zip"})
    else:
        # 単一ページの場合はPNG画像を返す
        p = int(page_num)
        image_bytes = pdf_loader.get_pdf_page_image(pdf_path, p)
        return StreamingResponse(image_bytes, media_type="image/png")


@router.get("/question-options")
def get_question_options():
    """
    質問テンプレートをカテゴリ・タグごとにグループ化して返すエンドポイント。
    """
    質問テンプレートをカテゴリ・タグごとにグループ化して返すエンドポイント。

    Returns:
        dict: カテゴリ・タグごとにグループ化されたテンプレート
    """
    # テンプレートデータの読み込み
    data = loader.load_question_templates()
    # カテゴリ・タグごとにグループ化
    grouped = loader.group_templates_by_category_and_tags(data)
    return grouped