"""
AI API Client - AIサービス内部HTTPクライアント

AIサービスと通信し、テキスト分類、感情分析、
エンティティ抽出などのAI機能を利用。

機能:
  - テキスト分類(カテゴリ判定)
  - 感情分析(ポジティブ/ネガティブ)
  - キーワード抽出
  - エンティティ認識(NER)

タイムアウト設定:
  - connect: 1.0s
  - read: 5.0s (AI処理は時間がかかる場合がある)
  - write: 5.0s
  - pool: 1.0s

使用例:
    client = AIClient()
    result = await client.classify("この製品は素晴らしいです")
    print(result['category'])  # 例: 'positive'
"""

import logging
import os
from typing import Optional

import httpx
from backend_shared.application.logging import create_log_context, get_module_logger

logger = get_module_logger(__name__)

AI_API_BASE = os.getenv("AI_API_BASE", "http://ai_api:8000")
TIMEOUT = httpx.Timeout(connect=1.0, read=5.0, write=5.0, pool=1.0)


class AIClient:
    """Client for AI API internal HTTP calls."""

    def __init__(self, base_url: str = AI_API_BASE):
        self.base_url = base_url.rstrip("/")

    async def classify(self, text: str) -> dict:
        """
        Classify text using AI API.

        Args:
            text: Input text to classify

        Returns:
            dict with classification result

        Raises:
            httpx.TimeoutException: If request times out
            httpx.HTTPStatusError: If AI API returns error status
        """
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            logger.info(
                "Calling AI API",
                extra=create_log_context(
                    operation="classify_text",
                    url=f"{self.base_url}/classify",
                    text_length=len(text),
                ),
            )
            response = await client.post(
                f"{self.base_url}/classify",
                json={"text": text},
            )
            response.raise_for_status()
            data = response.json()
            logger.info(
                "AI API response received",
                extra={"classification": data.get("category")},
            )
            return data

    async def get_health(self) -> dict:
        """Check AI API health status."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
