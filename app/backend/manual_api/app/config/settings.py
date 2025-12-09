"""
Manual API Settings - マニュアル参照API設定

backend_shared の BaseAppSettings を継承し、
Manual API 固有の設定を追加します。
"""
import os
from functools import lru_cache
from backend_shared.config.base_settings import BaseAppSettings


class ManualApiSettings(BaseAppSettings):
    """
    Manual API 設定クラス
    
    BaseAppSettings を継承し、Manual API 固有の設定を追加します。
    """
    
    # API基本情報
    API_TITLE: str = "MANUAL_API"
    API_VERSION: str = "1.0.0"
    
    # Manual API 固有設定
    MANUAL_FRONTEND_BASE_URL: str = os.getenv("MANUAL_FRONTEND_BASE_URL", "http://localhost:5173")
    """フロントエンドのベースURL（マニュアル用）"""
    
    MANUAL_ASSET_BASE_URL: str = os.getenv("MANUAL_ASSET_BASE_URL", "")
    """マニュアルアセットのベースURL"""
    
    MANUAL_ASSET_ROUTE: str = os.getenv("MANUAL_ASSET_ROUTE", "/assets/manuals")
    """マニュアルアセットのルート"""
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


@lru_cache(maxsize=1)
def get_settings() -> ManualApiSettings:
    """設定のシングルトンインスタンスを取得"""
    return ManualApiSettings()


# シングルトンインスタンス
settings = get_settings()

__all__ = ['settings', 'ManualApiSettings', 'get_settings']
