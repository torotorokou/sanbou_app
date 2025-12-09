"""
AI API Settings - AI サービス設定

backend_shared の BaseAppSettings を継承し、
AI API 固有の設定を追加します。
"""
import os
from functools import lru_cache
from backend_shared.config.base_settings import BaseAppSettings


class AiApiSettings(BaseAppSettings):
    """
    AI API 設定クラス
    
    BaseAppSettings を継承し、AI API 固有の設定を追加します。
    """
    
    # API基本情報
    API_TITLE: str = "AI API"
    API_VERSION: str = "1.0.0"
    
    # Gemini API Key
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


@lru_cache(maxsize=1)
def get_settings() -> AiApiSettings:
    """設定のシングルトンインスタンスを取得"""
    return AiApiSettings()


# シングルトンインスタンス
settings = get_settings()

# 後方互換性のため GEMINI_API_KEY を直接エクスポート
GEMINI_API_KEY = settings.GEMINI_API_KEY

__all__ = ['settings', 'AiApiSettings', 'get_settings', 'GEMINI_API_KEY']

