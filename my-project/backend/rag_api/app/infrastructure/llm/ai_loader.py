"""
AIによる回答生成のためのローダーモジュール。
OpenAIクライアント・ベクトルストア・JSONデータを組み合わせて回答を生成する。
"""

from app.infrastructure.llm.openai_client import generate_answer
from app.core.file_ingest_service import get_resource_paths, load_json_data
from app.utils.chunk_utils import load_faiss_vectorstore
from typing import List, Optional

def get_answer(query: str, category: str, tags: Optional[List[str]] = None):
    """
    クエリ・カテゴリ・タグをもとにAIによる回答を生成する。

    Args:
        query (str): ユーザーからの質問文
        category (str): 質問カテゴリ
        tags (Optional[List[str]]): タグリスト

    Returns:
        dict: 回答、参照元、ページ情報を含む辞書
    """
    paths = get_resource_paths()
    json_data = load_json_data(paths["JSON_PATH"])
    vectorstore = load_faiss_vectorstore(paths["FAISS_PATH"])
    result = generate_answer(query, category, json_data, vectorstore, tags)
    return {
        "answer": result["answer"],
        "sources": result["sources"],
        "pages": result["pages"]
    }