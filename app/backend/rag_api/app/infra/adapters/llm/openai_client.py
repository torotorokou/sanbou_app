"""
OpenAI APIを用いたAI回答生成クライアント。
"""

import os

from app.config.constants import build_prompt
from app.config.paths import CONFIG_ENV
from app.shared.chunk_utils import search_documents_with_category
from app.shared.env_loader import load_env_and_secrets
from dotenv import load_dotenv
from openai import OpenAI

print(f"[DEBUG] .env path: {CONFIG_ENV}")
load_dotenv(dotenv_path=str(CONFIG_ENV))
_secrets_loaded = load_env_and_secrets()
print(f"[DEBUG] secrets loaded from: {_secrets_loaded}")
_k = os.getenv("OPENAI_API_KEY")
masked = f"***{_k[-4:]}" if _k and len(_k) > 8 else ("set" if _k else "missing")
print(f"[DEBUG] OPENAI_API_KEY: {masked}")
client = OpenAI(api_key=_k)


def generate_answer(
    query: str,
    category: str,
    json_data: list[dict],
    vectorstore,
    tags: list[str] | None = None,
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
    try:
        print(
            "[DEBUG][openai_client] retrieved count:",
            len(retrieved) if isinstance(retrieved, list) else "unknown",
        )
    except Exception:
        pass
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
    # pages は int もしくは文字列トークン（例: "201-218" や "1,5,201-220"）を混在で保持し、
    # 下流の AIResponseService._normalize_pages で正規化・展開する。
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
            token = str(page_num).strip()
            if not token:
                continue
            # 単一数値は int に、それ以外（範囲や複合指定）は文字列トークンとして渡す
            if token.isdigit():
                try:
                    pages.append(int(token))
                except Exception:
                    # 念のため、失敗時は文字列で渡す
                    pages.append(token)
            else:
                pages.append(token)
    try:
        print(
            "[DEBUG][openai_client] pages extracted (raw):",
            pages[:10] if isinstance(pages, list) else pages,
        )
    except Exception:
        pass
    return {"answer": answer, "sources": sources, "pages": pages}
