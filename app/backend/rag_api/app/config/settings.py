"""
RAG API Settings - RAG/QAシステム設定

backend_shared の BaseAppSettings を継承し、
RAG API 固有の設定を追加します。
"""
import os
from functools import lru_cache
from backend_shared.config.base_settings import BaseAppSettings


class RagApiSettings(BaseAppSettings):
    """
    RAG API 設定クラス
    
    BaseAppSettings を継承し、RAG API 固有の設定を追加します。
    """
    
    # API基本情報
    API_TITLE: str = "RAG_API"
    API_VERSION: str = "1.0.0"
    API_ROOT_PATH: str = "/rag_api"
    
    # OpenAI API Key
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Secrets directory (backend_shared統一)
    SECRETS_DIR: str = os.getenv("SECRETS_DIR", "/backend/secrets")
    
    # GCP関連設定
    GCS_BUCKET_NAME: str = os.getenv("GCS_BUCKET_NAME", "object_haikibutu")
    GCS_DATA_PREFIX: str = os.getenv("GCS_DATA_PREFIX", "master")
    
    # デバッグ設定
    PERMISSION_DEBUG: bool = os.getenv("PERMISSION_DEBUG", "0") == "1"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


@lru_cache(maxsize=1)
def get_settings() -> RagApiSettings:
    """設定のシングルトンインスタンスを取得"""
    return RagApiSettings()


# シングルトンインスタンス
settings = get_settings()

__all__ = ['settings', 'RagApiSettings', 'get_settings']
