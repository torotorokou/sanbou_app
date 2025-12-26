"""
AIによる回答生成のためのローダーモジュール。
OpenAIクライアント・ベクトルストア・JSONデータを組み合わせて回答を生成する。
"""

import os

from openai import RateLimitError

from app.core.usecases.rag.file_ingest_service import get_resource_paths, load_json_data
from app.infra.adapters.llm.openai_client import generate_answer
from app.shared.chunk_utils import load_faiss_vectorstore
from backend_shared.application.logging import get_module_logger


logger = get_module_logger(__name__)


def get_answer(
    query: str,
    category: str,
    tags: list[str] | None = None,
    *,
    answer_func=generate_answer,
    resource_paths_func=get_resource_paths,
    json_loader=load_json_data,
    vectorstore_loader=load_faiss_vectorstore,
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
            成功時: {"answer": str, "sources": list, "pages": any}
            失敗時: {"error": str, "answer": None, "sources": [], "pages": None}
    """
    try:
        paths = resource_paths_func()
        json_path = str(paths.get("JSON_PATH"))
        faiss_path = str(paths.get("FAISS_PATH"))
        logger.debug(
            "resource paths: %s",
            {"JSON_PATH": json_path, "FAISS_PATH": faiss_path},
        )

        # ファイル存在チェック
        json_exists = os.path.exists(json_path)
        faiss_exists = os.path.exists(faiss_path)
        logger.debug(
            "exists: %s",
            {
                "json_exists": json_exists,
                "faiss_exists": faiss_exists,
            },
        )

        # どちらかのファイルが存在しない場合は早期リターン
        if not json_exists or not faiss_exists:
            missing = []
            if not json_exists:
                missing.append("JSONファイル")
            if not faiss_exists:
                missing.append("FAISSベクトルストア")
            error_msg = f"必要なデータファイルが見つかりません: {', '.join(missing)}"
            logger.debug(error_msg)
            return {"error": error_msg, "answer": None, "sources": [], "pages": None}

        json_data = json_loader(json_path)
        vectorstore = vectorstore_loader(faiss_path)
        result = answer_func(query, category, json_data, vectorstore, tags)
        # 重要キーの存在とサイズを軽く記録（型安全な集計）
        if isinstance(result, dict):
            pages = result.get("pages")
            sources = result.get("sources")
            sources_len = len(sources) if isinstance(sources, list) else 0
            pages_len = len(pages) if isinstance(pages, list) else 0
            logger.debug(
                "answer_func returned: %s",
                {
                    "has_answer": bool(result.get("answer")),
                    "sources_len": sources_len,
                    "pages_len": pages_len,
                },
            )
        return {
            "answer": result["answer"],
            "sources": result["sources"],
            "pages": result["pages"],
        }
    except RateLimitError as rate_err:
        # OpenAI RateLimitError（insufficient_quota等）
        error_msg = str(rate_err)
        logger.warning("RateLimitError: %r", rate_err)

        # insufficient_quotaの判定
        error_code = "OPENAI_RATE_LIMIT"
        if "insufficient_quota" in error_msg.lower():
            error_code = "OPENAI_INSUFFICIENT_QUOTA"

        return {
            "error": error_msg,
            "error_code": error_code,
            "answer": None,
            "sources": [],
            "pages": None,
        }
    except Exception as e:
        # その他の予期しない例外
        logger.error("error: %r", e)
        return {
            "error": str(e),
            "error_code": "OPENAI_ERROR",
            "answer": None,
            "sources": [],
            "pages": None,
        }
