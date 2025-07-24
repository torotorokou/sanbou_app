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
        # rがdict型（metadata）の場合
        if isinstance(r, dict):
            source = r.get("source")
            page_num = r.get("page") or r.get("PAGE")
        # rが3要素タプル (source, content, metadata) の場合
        elif len(r) > 2 and isinstance(r[2], dict):
            source = r[0]
            page_num = r[2].get("page") or r[2].get("PAGE")
        # rが2要素タプル (source, metadata) の場合
        elif len(r) == 2 and isinstance(r[1], dict):
            source = r[0]
            page_num = r[1].get("page") or r[1].get("PAGE")
        else:
            source = r[0]
            page_num = None
        sources.append(source)
        if page_num is not None and page_num != "":
            try:
                page_num_int = int(page_num)
            except Exception:
                page_num_int = page_num
            pages.append(str(page_num_int))
    return {"answer": answer, "sources": sources, "pages": pages}
