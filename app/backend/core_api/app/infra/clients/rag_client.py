"""
RAG API Client - RAGサービス内部HTTPクライアント

RAG(Retrieval-Augmented Generation)サービスと通信し、
ドキュメント検索と生成AIを組み合わせた質問応答を実現。

機能:
  - ユーザーの質問にAIが回答
  - 関連ドキュメントの検索と参照
  - 回答の根拠となるソース情報を付与

タイムアウト設定:
  - connect: 1.0s (接続確立)
  - read: 5.0s (レスポンス読み取り)
  - write: 5.0s (リクエスト送信)
  - pool: 1.0s (コネクションプール)

使用例:
    client = RAGClient()
    result = await client.ask("搬入手順を教えてください")
    print(result['answer'])
    print(result['sources'])  # 参照ドキュメント
"""

import os

import httpx
from backend_shared.application.logging import get_module_logger

logger = get_module_logger(__name__)

RAG_API_BASE = os.getenv("RAG_API_BASE", "http://rag_api:8000")
# OpenAIの応答待ち時間を考慮してタイムアウトを長めに設定
TIMEOUT = httpx.Timeout(connect=2.0, read=60.0, write=10.0, pool=2.0)


class RAGClient:
    """Client for RAG API internal HTTP calls."""

    def __init__(self, base_url: str = RAG_API_BASE):
        self.base_url = base_url.rstrip("/")

    async def ask(
        self, query: str, category: str = "shogun", tags: list[str] | None = None
    ) -> dict:
        """
        Ask RAG API a question.

        Args:
            query: User query string
            category: Question category (default: "shogun")
            tags: List of tags (default: None)

        Returns:
            dict with 'answer' and optional 'sources'

        Raises:
            httpx.TimeoutException: If request times out
            httpx.HTTPStatusError: If RAG API returns error status
        """
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            logger.info(
                f"Calling RAG API: {self.base_url}/api/generate-answer",
                extra={"query": query},
            )
            response = await client.post(
                f"{self.base_url}/api/generate-answer",
                json={"query": query, "category": category, "tags": tags or []},
            )
            response.raise_for_status()
            data = response.json()

            # レスポンス形式の正規化 (SuccessApiResponse or direct dict)
            result = data.get("result", data)

            logger.info(
                "RAG API response received",
                extra={"answer_length": len(result.get("answer", ""))},
            )
            return {
                "answer": result.get("answer", ""),
                "sources": result.get("sources", []),
            }
