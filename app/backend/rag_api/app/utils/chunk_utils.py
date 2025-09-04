from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from typing import List, Optional, Any, Dict
import ast
import os

def load_faiss_vectorstore(faiss_path: str) -> Any:
    embeddings = OpenAIEmbeddings()
    return FAISS.load_local(str(faiss_path), embeddings, allow_dangerous_deserialization=True)

def safe_parse_tags(raw: Any) -> List[Any]:
    """与えられたタグフィールドを確実にリストへ正規化する。

    受け入れる形式:
    - list → そのまま
    - 単一の値（str, int 等）→ [value]
    - 文字列のリスト表現 "['A','B']" → ['A','B']
    - カンマ区切り文字列 "A,B" → ['A','B']
    """
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        s = raw.strip()
        # まず Python リテラルとして評価を試みる
        try:
            parsed = ast.literal_eval(s)
            if isinstance(parsed, list):
                return parsed
            return [parsed]
        except Exception:
            # カンマ区切りの簡易対応
            if "," in s:
                parts = [p.strip() for p in s.split(",") if p.strip()]
                if parts:
                    return parts
            if s:
                return [s]
            return []
    # その他の型は単一値として扱う
    return [raw] if raw is not None else []

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
    top_k: int = 12,
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
    DEBUG_VERBOSE = os.environ.get("RAG_DEBUG_VERBOSE") == "1"

    # JSON データからタグを引くための簡易インデックス（title と chunk_id をキーに）
    title_to_tags: Dict[str, List[Any]] = {}
    chunk_to_tags: Dict[str, List[Any]] = {}
    if isinstance(json_data, list):
        for item in json_data:
            try:
                t = item.get("title")
                c = item.get("chunk_id")
                tg = item.get("tags") or item.get("tag") or []
                tg_list = safe_parse_tags(tg)
                if t:
                    title_to_tags.setdefault(str(t), []).extend(tg_list)
                if c:
                    chunk_to_tags.setdefault(str(c), []).extend(tg_list)
            except Exception:
                pass

    for doc, score in results:
        meta = doc.metadata
        doc_category_raw = meta.get("category")
        # support both 'tag' and 'tags' keys (some sources use 'tags')
        doc_tags_raw = meta.get("tag", None)
        if doc_tags_raw is None:
            doc_tags_raw = meta.get("tags", [])

        if DEBUG_VERBOSE:
            try:
                print("[DEBUG][search] doc.metadata keys:", list(meta.keys()))
                print("[DEBUG][search] meta.tag=", repr(meta.get("tag")), " meta.tags=", repr(meta.get("tags")))
            except Exception:
                pass

        # カテゴリ正規化（リストも考慮して包含判定）
        if isinstance(doc_category_raw, list):
            doc_categories = [_normalize_token(x) for x in doc_category_raw]
        else:
            doc_categories = [_normalize_token(doc_category_raw)]

        # タグ正規化 + JSON 側のタグも常に統合（メタタグがあっても JSON タグを併用）
        base_tags_list = safe_parse_tags(doc_tags_raw)
        # title と chunk_id で JSON のタグを検索
        title = meta.get("title")
        chunk_id = meta.get("chunk_id") or meta.get("CHUNK_ID")
        json_tags: List[Any] = []
        if title and title in title_to_tags:
            json_tags.extend(title_to_tags.get(title, []))
        if chunk_id and chunk_id in chunk_to_tags:
            json_tags.extend(chunk_to_tags.get(chunk_id, []))
        # 和集合（重複除去は正規化後に set で）
        combined_list = list(base_tags_list) + list(json_tags)
        if DEBUG_VERBOSE:
            try:
                print("[DEBUG][search] title:", title, "chunk_id:", chunk_id)
                print("[DEBUG][search] base_tags:", base_tags_list, " json_tags:", json_tags)
            except Exception:
                pass
        doc_tags_norm = set(_normalize_token(t) for t in combined_list)

        if DEBUG_VERBOSE:
            try:
                print("[DEBUG][search] doc_tags_norm:", doc_tags_norm)
                print("[DEBUG][search] norm_query_tags:", norm_query_tags)
            except Exception:
                pass

        # マッチ条件
        cat_match = norm_category in doc_categories
        tags_ok = (not norm_query_tags) or bool(norm_query_tags & doc_tags_norm)

        if cat_match and tags_ok:
            filtered.append((meta.get("title", "Unknown"), doc.page_content, meta))

    try:
        print("[DEBUG][search] filtered hits:", len(filtered), "category=", category, "tags=", tags)
    except Exception:
        pass

    # JSON データからカテゴリ・タグ一致で候補を合成（ベクトル結果に統合）
    json_candidates_scored: List[tuple] = []
    if isinstance(json_data, list):
        for item in json_data:
            try:
                item_cat_raw = item.get("category")
                if isinstance(item_cat_raw, list):
                    item_cats = [_normalize_token(x) for x in item_cat_raw]
                else:
                    item_cats = [_normalize_token(item_cat_raw)]
                if norm_category not in item_cats:
                    continue
                item_tags = safe_parse_tags(item.get("tags") or item.get("tag") or [])
                item_tags_norm = set(_normalize_token(t) for t in item_tags)
                if norm_query_tags and not (norm_query_tags & item_tags_norm):
                    continue
                meta = {
                    "title": item.get("title", "Unknown"),
                    "category": item.get("category"),
                    "tags": item.get("tags") or item.get("tag") or [],
                    "chunk_id": item.get("chunk_id"),
                    "page": item.get("page"),
                    "source": "json_candidate",
                }
                content = item.get("content")
                if isinstance(content, list):
                    page_content = "\n".join([str(c) for c in content])
                else:
                    page_content = str(content)
                # 簡易スコア: タイトル完全一致・キーワード含有・タグ一致数
                title = str(meta.get("title", ""))
                q_norm = _normalize_token(query)
                title_norm = _normalize_token(title)
                score = 0
                if title_norm == q_norm:
                    score += 100
                # 代表的キーワード（面積 等）を優先。日本語はそのまま部分一致。
                key_tokens = ["面積"]
                for kt in key_tokens:
                    if kt in query and kt in title:
                        score += 10
                    elif kt in query and kt in page_content:
                        score += 8
                    elif kt in title:
                        score += 6
                score += len(norm_query_tags & item_tags_norm)
                json_candidates_scored.append((score, (meta.get("title", "Unknown"), page_content, meta)))
            except Exception:
                continue
    if json_candidates_scored:
        try:
            print("[DEBUG][search] json candidates (scored):", len(json_candidates_scored))
        except Exception:
            pass
        # スコア順に並べ替え（降順）
        json_candidates_scored.sort(key=lambda x: x[0], reverse=True)
        json_candidates = [tpl for _, tpl in json_candidates_scored]
        # ベクトル結果と統合（title+chunk_id で重複除去）
        seen = set()
        merged: List[tuple] = []
        def key_of(tpl: tuple):
            m = tpl[2] if len(tpl) > 2 and isinstance(tpl[2], dict) else {}
            return (m.get("title"), m.get("chunk_id"))
        for tpl in filtered:
            k = key_of(tpl)
            if k not in seen:
                seen.add(k)
                merged.append(tpl)
        for tpl in json_candidates:
            k = key_of(tpl)
            if k not in seen:
                seen.add(k)
                merged.append(tpl)
        if merged:
            return merged[:top_k]

    # フォールバック2: それでも0件ならカテゴリのみで再評価
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