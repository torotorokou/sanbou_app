"""
AI API Client - Internal HTTP client for AI service.
"""
import os
import httpx
from typing import Optional
import logging

logger = logging.getLogger(__name__)

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
            logger.info(f"Calling AI API: {self.base_url}/classify", extra={"text_length": len(text)})
            response = await client.post(
                f"{self.base_url}/classify",
                json={"text": text},
            )
            response.raise_for_status()
            data = response.json()
            logger.info("AI API response received", extra={"classification": data.get("category")})
            return data

    async def get_health(self) -> dict:
        """Check AI API health status."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
