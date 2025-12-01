import requests
from backend_shared.core.domain.exceptions import ExternalServiceError
from app.config.settings import GEMINI_API_KEY

class GeminiClient:
    def generate_content(self, prompt: str) -> str:
        try:
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
                f"?key={GEMINI_API_KEY}"
            )
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json={"contents": [{"parts": [{"text": prompt}]}]},
            )
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except requests.exceptions.RequestException as e:
            # Gemini API通信エラー
            raise ExternalServiceError(
                service_name="Gemini API",
                message=f"Communication failed: {str(e)}",
                status_code=getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None,
                cause=e
            )
        except (KeyError, IndexError) as e:
            # レスポンス形式が不正
            raise ExternalServiceError(
                service_name="Gemini API",
                message=f"Unexpected response format: {str(e)}",
                cause=e
            )
