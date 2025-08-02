from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from typing import List, Optional
import ast

def load_faiss_vectorstore(faiss_path):
from typing import List, Optional, Any

def load_faiss_vectorstore(faiss_path: str) -> Any:
    embeddings = OpenAIEmbeddings()
    return FAISS.load_local(str(faiss_path), embeddings, allow_dangerous_deserialization=True)

def safe_parse_tags(raw):
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
        except:
            return [raw]
    return []

def search_documents_with_category(
    query: str,
    category: str,
    json_data: List[dict],
    vectorstore: Any,
    top_k: int = 4,
    tags: Optional[List[str]] = None
) -> List[tuple]:
    results = vectorstore.similarity_search_with_score(query, k=top_k)
    filtered = []

    for doc, score in results:
        meta = doc.metadata
        doc_category_raw = meta.get("category")
        doc_tags_raw = meta.get("tag", [])

        if isinstance(doc_category_raw, list):
            doc_category = doc_category_raw[0] if doc_category_raw else ""
        else:
            doc_category = str(doc_category_raw)

        doc_tags = safe_parse_tags(doc_tags_raw)

        if doc_category == category:
            if tags is None or any(tag in doc_tags for tag in tags):
                filtered.append((meta.get("title", "Unknown"), doc.page_content, meta))

    return filtered