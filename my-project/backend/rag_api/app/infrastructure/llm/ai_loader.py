"""
AIによる回答生成のためのローダーモジュール。
OpenAIクライアント・ベクトルストア・JSONデータを組み合わせて回答を生成する。
"""

from app.infrastructure.llm.openai_client import generate_answer
from app.core.file_ingest_service import get_resource_paths, load_json_data
from app.utils.chunk_utils import load_faiss_vectorstore
from typing import List, Optional


def get_answer(
    query: str,
    category: str,
    tags: Optional[List[str]] = None,
    *,
    answer_func=generate_answer,
    resource_paths_func=get_resource_paths,
    json_loader=load_json_data,
    vectorstore_loader=load_faiss_vectorstore
) -> dict:
    """
    クエリ・カテゴリ・タグをもとにAIによる回答を生成する。
    依存関数を引数で注入できるため、テストや拡張が容易。

    Args:
        query (str): ユーザーからの質問文
        category (str): 質問カテゴリ
        tags (Optional[List[str]]): タグリスト
        answer_func: 回答生成関数（デフォルト: generate_answer）
        resource_paths_func: リソースパス取得関数
        json_loader: JSONローダー
        vectorstore_loader: ベクトルストアローダー

    Returns:
        dict: 回答、参照元、ページ情報を含む辞書
    """
    try:
        paths = resource_paths_func()
        json_data = json_loader(paths["JSON_PATH"])
        vectorstore = vectorstore_loader(paths["FAISS_PATH"])
        result = answer_func(query, category, json_data, vectorstore, tags)
        return {
            "answer": result["answer"],
            "sources": result["sources"],
            "pages": result["pages"]
        }
    except Exception as e:
        # ログ出力やエラー通知など拡張ポイント
        return {"error": str(e)}