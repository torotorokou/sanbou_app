"""
OpenAI APIを用いたAI回答生成クライアント。
"""

from typing import List, Optional
from app.utils.chunk_utils import search_documents_with_category
from app.local_config.constants import build_prompt
from openai import OpenAI
import os
from dotenv import load_dotenv
from app.paths import CONFIG_ENV

print(f"[DEBUG] .env path: {CONFIG_ENV}")
load_dotenv(dotenv_path=str(CONFIG_ENV))
_k = os.getenv("OPENAI_API_KEY")
masked = f"***{_k[-4:]}" if _k and len(_k) > 8 else ("set" if _k else "missing")
print(f"[DEBUG] OPENAI_API_KEY: {masked}")
client = OpenAI(api_key=_k)


def generate_answer(
    query: str,
    category: str,
    json_data: List[dict],
    vectorstore,
    tags: Optional[List[str]] = None,
) -> dict:
    """
    クエリ・カテゴリ・タグをもとにAI回答を生成する。

    Args:
        query (str): 質問文
        category (str): カテゴリ
        json_data (List[dict]): 検索対象データ
        vectorstore: ベクトルストア
        tags (Optional[List[str]]): タグリスト

    Returns:
        dict: 回答、参照元、ページ情報
    """
    retrieved = search_documents_with_category(
        query, category, json_data, vectorstore, tags=tags
    )
    context = "\n".join([r[1] for r in retrieved])
    prompt = build_prompt(query, context)
    response = client.chat.completions.create(
        model="gpt-4", messages=[{"role": "user", "content": prompt}]
    )
    content = (
        response.choices[0].message.content
        if response.choices and response.choices[0].message
        else ""
    )
    answer = (content or "").strip()
    sources = []
    pages = []
    for r in retrieved:
        if isinstance(r, dict):
            source = r.get("source")
            page_num = (
                r.get("page")
                or r.get("PAGE")
                or r.get("page_number")
                or r.get("PAGE_NUMBER")
            )
        elif isinstance(r, (list, tuple)) and len(r) > 2 and isinstance(r[2], dict):
            source = r[0]
            meta = r[2]
            page_num = (
                meta.get("page")
                or meta.get("PAGE")
                or meta.get("page_number")
                or meta.get("PAGE_NUMBER")
            )
        elif isinstance(r, (list, tuple)) and len(r) == 2 and isinstance(r[1], dict):
            source = r[0]
            meta = r[1]
            page_num = (
                meta.get("page")
                or meta.get("PAGE")
                or meta.get("page_number")
                or meta.get("PAGE_NUMBER")
            )
        elif isinstance(r, (list, tuple)) and len(r) >= 1:
            source = r[0]
            page_num = None
        else:
            # 不明な形式はスキップ
            continue
        sources.append(source)
        if page_num is not None and page_num != "":
            try:
                page_num_int = int(str(page_num).strip())
            except Exception:
                # ページが特定できない場合はスキップ（空白PDFの原因回避）
                continue
            # 正規化: 下流は0/1両対応済み
            pages.append(page_num_int)
    return {"answer": answer, "sources": sources, "pages": pages}
