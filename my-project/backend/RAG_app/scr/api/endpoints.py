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

@router.get("/pdf-page")
def pdf_page(pdf_path: str, page_num: int):
    image_bytes = get_pdf_page_image(pdf_path, page_num)
    return StreamingResponse(image_bytes, media_type="image/png")

@router.get("/question-options")
def get_question_options():
    paths = loader.get_resource_paths()
    data = loader.load_question_templates()
    grouped = loader.group_templates_by_category_and_tags(data)
    return grouped
