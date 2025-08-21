from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from typing import List, Optional, Any
import ast

def load_faiss_vectorstore(faiss_path: str) -> Any:
    embeddings = OpenAIEmbeddings()
    return FAISS.load_local(str(faiss_path), embeddings, allow_dangerous_deserialization=True)

def safe_parse_tags(raw: Any) -> List[Any]:
    if isinstance(raw, list):
        return raw
    elif isinstance(raw, str):
        try:
            parsed = ast.literal_eval(raw)
            if isinstance(parsed, list):
                return parsed
            else:
                return [parsed]
        except Exception:
            return [raw]
    return []

def _normalize_token(s: Any) -> str:
    try:
        # 前後空白を除去し、簡易に小文字化（英数用）。日本語には影響軽微。
        return str(s).strip().lower()
    except Exception:
        return str(s)

def search_documents_with_category(
    query: str,
    category: str,
    json_data: List[dict],
    vectorstore: Any,
    top_k: int = 4,
    tags: Optional[List[str]] = None
) -> List[tuple]:
    results = vectorstore.similarity_search_with_score(query, k=top_k)
    try:
        print("[DEBUG][search] raw hits:", len(results))
    except Exception:
        pass
    filtered = []
    norm_category = _normalize_token(category)
    norm_query_tags = set(_normalize_token(t) for t in (tags or []))

    for doc, score in results:
        meta = doc.metadata
        doc_category_raw = meta.get("category")
        doc_tags_raw = meta.get("tag", [])

        # カテゴリ正規化（リストも考慮して包含判定）
        if isinstance(doc_category_raw, list):
            doc_categories = [_normalize_token(x) for x in doc_category_raw]
        else:
            doc_categories = [_normalize_token(doc_category_raw)]

        # タグ正規化
        doc_tags_list = safe_parse_tags(doc_tags_raw)
        doc_tags_norm = set(_normalize_token(t) for t in doc_tags_list)

        # マッチ条件
        cat_match = norm_category in doc_categories
        tags_ok = (not norm_query_tags) or bool(norm_query_tags & doc_tags_norm)

        if cat_match and tags_ok:
            filtered.append((meta.get("title", "Unknown"), doc.page_content, meta))

    try:
        print("[DEBUG][search] filtered hits:", len(filtered), "category=", category, "tags=", tags)
    except Exception:
        pass

    # フォールバック: 0件ならカテゴリのみで再評価
    if not filtered:
        category_only = []
        for doc, score in results:
            meta = doc.metadata
            doc_category_raw = meta.get("category")
            if isinstance(doc_category_raw, list):
                doc_categories = [_normalize_token(x) for x in doc_category_raw]
            else:
                doc_categories = [_normalize_token(doc_category_raw)]
            if norm_category in doc_categories:
                category_only.append((meta.get("title", "Unknown"), doc.page_content, meta))
        if category_only:
            print("[DEBUG][search] fallback: category-only hits:", len(category_only))
            return category_only

    # それでも0件なら生ヒットを返す（上位top_k、観察用）
    if not filtered:
        raw_mapped = []
        for doc, score in results:
            meta = doc.metadata
            raw_mapped.append((meta.get("title", "Unknown"), doc.page_content, meta))
        print("[DEBUG][search] fallback: raw mapped hits:", len(raw_mapped))
        return raw_mapped

    return filtered