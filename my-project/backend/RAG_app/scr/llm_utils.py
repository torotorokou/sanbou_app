from typing import List, Tuple, Optional
from scr.prompts import build_prompt
from scr.utils import search_documents_with_category
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../config/.env"))

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_answer(query: str, category: str, json_data: List[dict], vectorstore, tags: Optional[List[str]] = None) -> dict:
    retrieved = search_documents_with_category(query, category, json_data, vectorstore, tags=tags)
    context = "\n".join([r[1] for r in retrieved])
    prompt = build_prompt(query, context)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    answer = response.choices[0].message.content.strip()
    # sources, pages情報を抽出
    sources = []
    pages = []
    for r in retrieved:
        # r[0]: source, r[2]: metadata (dict)
        source = r[0]
        meta = r[2] if len(r) > 2 else {}
        # 大文字・小文字両対応
        pdf_path = (
            meta.get("pdf_path") or meta.get("PDF_PATH") or
            meta.get("path") or meta.get("PATH") or
            meta.get("file_path") or meta.get("FILE_PATH")
        )
        page_num = meta.get("page") or meta.get("PAGE")
        sources.append(source)
        if pdf_path is not None and page_num is not None:
            try:
                page_num_int = int(page_num)
            except Exception:
                page_num_int = page_num
            pages.append({"pdf_path": str(pdf_path), "page_num": page_num_int})
    return {"answer": answer, "sources": sources, "pages": pages}
