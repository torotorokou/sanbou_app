"""
AIによる回答生成のためのローダーモジュール。
OpenAIクライアント・ベクトルストア・JSONデータを組み合わせて回答を生成する。
"""

from app.infrastructure.llm.openai_client import generate_answer
from app.core.file_ingest_service import get_resource_paths, load_json_data
from app.utils.chunk_utils import load_faiss_vectorstore
from typing import List, Optional
import os


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
        json_path = str(paths.get("JSON_PATH"))
        faiss_path = str(paths.get("FAISS_PATH"))
        print(
            "[DEBUG][ai_loader] resource paths:",
            {"JSON_PATH": json_path, "FAISS_PATH": faiss_path},
        )
        print(
            "[DEBUG][ai_loader] exists:",
            {
                "json_exists": os.path.exists(json_path),
                "faiss_exists": os.path.exists(faiss_path),
            },
        )

        json_data = json_loader(json_path)
        vectorstore = vectorstore_loader(faiss_path)
        result = answer_func(query, category, json_data, vectorstore, tags)
        # 重要キーの存在とサイズを軽く記録（型安全な集計）
        if isinstance(result, dict):
            pages = result.get("pages")
            sources = result.get("sources")
            sources_len = len(sources) if isinstance(sources, list) else 0
            pages_len = len(pages) if isinstance(pages, list) else 0
            print(
                "[DEBUG][ai_loader] answer_func returned:",
                {"has_answer": bool(result.get("answer")), "sources_len": sources_len, "pages_len": pages_len},
            )
        return {
            "answer": result["answer"],
            "sources": result["sources"],
            "pages": result["pages"]
        }
    except Exception as e:
        # ログ出力やエラー通知など拡張ポイント
        print("[DEBUG][ai_loader] error:", repr(e))
        return {"error": str(e)}