from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from scr.api.models import QueryRequest, QueryResponse
from scr import ai_loader, loader
from scr.pdf_utils import get_pdf_page_image

router = APIRouter()

@router.post("/generate-answer", response_model=QueryResponse)
async def generate_answer(request: QueryRequest):
    result = ai_loader.get_answer(request.query, request.category, request.tags)
    return QueryResponse(answer=result["answer"], sources=result["sources"], pages=result["pages"])

import io
import zipfile
from fastapi.responses import StreamingResponse

@router.get("/pdf-page")
def pdf_page(page_num: str):
    # scr.pathsからPDF_PATHを取得
    from scr.paths import PDF_PATH
    pdf_path = str(PDF_PATH)

    # ページ範囲対応（例: "177-190"）
    if '-' in page_num:
        start, end = page_num.split('-')
        start = int(start)
        end = int(end)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zipf:
            for p in range(start, end + 1):
                img_bytes = get_pdf_page_image(pdf_path, p)
                zipf.writestr(f'page_{p}.png', img_bytes.getvalue())
        buf.seek(0)
        return StreamingResponse(buf, media_type="application/zip", headers={"Content-Disposition": "attachment; filename=pages.zip"})
    else:
        p = int(page_num)
        image_bytes = get_pdf_page_image(pdf_path, p)
        return StreamingResponse(image_bytes, media_type="image/png")

@router.get("/question-options")
def get_question_options():
    paths = loader.get_resource_paths()
    data = loader.load_question_templates()
    grouped = loader.group_templates_by_category_and_tags(data)
    return grouped
