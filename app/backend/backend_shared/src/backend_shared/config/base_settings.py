"""
Base Application Settings - 共通アプリケーション設定

【概要】
全バックエンドサービスで共通する設定の基底クラスです。
各サービスはこのクラスを継承して独自の設定を追加します。

【主な機能】
1. ステージ設定（dev/stg/prod）
2. デバッグモード設定
3. API基本情報（タイトル、バージョン、ルートパス）
4. CORS設定

【設計方針】
- Pydantic BaseSettings を使用した型安全な設定管理
- 環境変数から自動的に値を読み込み
- デフォルト値の提供により開発環境でも動作
- 各サービスで継承して拡張可能

【使用例】
```python
# 各サービスの settings.py で継承
from backend_shared.config.base_settings import BaseAppSettings

class CoreApiSettings(BaseAppSettings):
    API_TITLE: str = "CORE_API"

    # サービス固有の設定を追加
    DATABASE_URL: str = "..."

def get_settings() -> CoreApiSettings:
    return CoreApiSettings()
```
"""

import os
from functools import lru_cache

from pydantic_settings import BaseSettings

from backend_shared.config.env_utils import get_stage, is_debug_mode


class BaseAppSettings(BaseSettings):
    """
    全サービス共通の基本設定

    各サービスはこのクラスを継承して独自設定を追加します。
    環境変数から自動的に値を読み込み、型変換・検証を行います。

    Attributes:
        STAGE: デプロイ環境（dev/stg/prod）
        DEBUG: デバッグモード（True で /docs 等を公開）
        API_TITLE: API タイトル
        API_VERSION: API バージョン
        API_ROOT_PATH: API ルートパス
        CORS_ORIGINS: CORS許可オリジン（カンマ区切り）

    Examples:
        >>> settings = BaseAppSettings()
        >>> settings.STAGE
        'dev'
        >>> settings.DEBUG
        True
        >>> settings.cors_origins_list
        ['http://localhost:5173', 'http://127.0.0.1:5173']
    """

    # ========================================
    # ステージ設定
    # ========================================

    STAGE: str = get_stage()
    """
    デプロイ環境（dev/stg/prod）

    環境変数 STAGE で設定可能。
    デフォルトは 'dev'。
    """

    DEBUG: bool = is_debug_mode()
    """
    デバッグモード（True で /docs 等を公開）

    環境変数 DEBUG で設定可能。
    本番環境では必ず False にしてください。
    """

    # ========================================
    # API基本情報
    # ========================================

    API_TITLE: str = "API Service"
    """
    API タイトル

    各サービスで上書きしてください。
    例: "CORE_API", "LEDGER_API"
    """

    API_VERSION: str = "1.0.0"
    """
    API バージョン

    環境変数 API_VERSION で上書き可能。
    """

    API_ROOT_PATH: str = ""
    """
    API ルートパス

    BFF経由の場合は /core_api などを設定します。
    環境変数 API_ROOT_PATH で上書き可能。
    """

    # ========================================
    # CORS設定
    # ========================================

    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    """
    CORS許可オリジン（カンマ区切り）

    環境変数 CORS_ORIGINS で設定可能。
    本番環境では必ず明示的なオリジンリストを設定してください。
    """

    @property
    def cors_origins_list(self) -> list[str]:
        """
        CORS許可オリジンをリストで取得

        カンマ区切りの文字列を自動的にリストに変換します。
        空白は自動的にトリムされます。

        Returns:
            list[str]: CORS許可オリジンのリスト

        Examples:
            >>> settings = BaseAppSettings(CORS_ORIGINS="http://example.com , http://localhost:3000 ")
            >>> settings.cors_origins_list
            ['http://example.com', 'http://localhost:3000']
        """
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # ========================================
    # アプリケーション設定
    # ========================================

    APP_TIMEZONE: str = os.getenv("APP_TIMEZONE", "Asia/Tokyo")
    """
    アプリケーション全体で使用するタイムゾーン

    環境変数 APP_TIMEZONE で設定可能。
    デフォルトは 'Asia/Tokyo'。
    """

    # ========================================
    # Pydantic 設定
    # ========================================

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # 追加の環境変数を許可
        validate_default = True


@lru_cache(maxsize=1)
def get_base_settings() -> BaseAppSettings:
    """
    基本設定のシングルトンインスタンスを取得

    アプリケーション起動時に一度だけ設定を読み込み、
    以降はキャッシュされたインスタンスを返します。

    Returns:
        BaseAppSettings: 基本設定のインスタンス

    Examples:
        >>> settings1 = get_base_settings()
        >>> settings2 = get_base_settings()
        >>> settings1 is settings2
        True
    """
    return BaseAppSettings()


__all__ = [
    "BaseAppSettings",
    "get_base_settings",
]
