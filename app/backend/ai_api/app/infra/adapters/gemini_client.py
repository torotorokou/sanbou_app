import os

import requests
from app.config.settings import GEMINI_API_KEY
from backend_shared.application.logging import get_module_logger
from backend_shared.core.domain.exceptions import ExternalServiceError

logger = get_module_logger(__name__)


class GeminiClient:
    def generate_content(self, prompt: str) -> str:
        logger.info(
            "Generating content with Gemini API", extra={"prompt_length": len(prompt)}
        )
        try:
            # 環境変数から Gemini API URL を取得（デフォルト値付き）
            gemini_api_url = os.getenv(
                "GEMINI_API_URL",
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
            )
            url = f"{gemini_api_url}?key={GEMINI_API_KEY}"
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json={"contents": [{"parts": [{"text": prompt}]}]},
            )
            response.raise_for_status()
            data = response.json()
            result = data["candidates"][0]["content"]["parts"][0]["text"]
            logger.info(
                "Successfully generated content", extra={"response_length": len(result)}
            )
            return result
        except requests.exceptions.RequestException as e:
            # Gemini API通信エラー
            logger.error(
                "Gemini API communication failed",
                exc_info=True,
                extra={"error": str(e)},
            )
            raise ExternalServiceError(
                service_name="Gemini API",
                message=f"Communication failed: {str(e)}",
                status_code=(
                    getattr(e.response, "status_code", None)
                    if hasattr(e, "response")
                    else None
                ),
                cause=e,
            )
        except (KeyError, IndexError) as e:
            # レスポンス形式が不正
            logger.error(
                "Gemini API response format error",
                exc_info=True,
                extra={"error": str(e)},
            )
            raise ExternalServiceError(
                service_name="Gemini API",
                message=f"Unexpected response format: {str(e)}",
                cause=e,
            )
