"""
Plan Worker Settings - 予測ワーカー設定

backend_shared の BaseAppSettings を継承し、
Plan Worker 固有の設定を追加します。
"""

import os
from functools import lru_cache

from pydantic import Field

from backend_shared.config.base_settings import BaseAppSettings
from backend_shared.infra.db.url_builder import build_database_url_with_driver


def _build_database_url() -> str:
    """環境変数からDATABASE_URLを構築（SQLAlchemy用）"""
    return build_database_url_with_driver(driver="psycopg")


class PlanWorkerSettings(BaseAppSettings):
    """
    Plan Worker 設定クラス

    BaseAppSettings を継承し、Plan Worker 固有の設定を追加します。
    """

    # API基本情報
    API_TITLE: str = "Plan Worker"
    API_VERSION: str = "1.0.0"

    # Plan Worker 固有設定
    database_url: str = Field(default_factory=_build_database_url)
    """データベース接続URL（自動構築）"""

    lookback_years: int = Field(default=int(os.getenv("LOOKBACK_YEARS", "5")))
    """予測に使用する過去データの年数"""

    log_level: str = Field(default=os.getenv("LOG_LEVEL", "INFO"))
    """ログレベル（DEBUG/INFO/WARNING/ERROR/CRITICAL）"""

    poll_interval: int = Field(default=int(os.getenv("POLL_INTERVAL", "5")))
    """ジョブポーリング間隔（秒）"""

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


@lru_cache(maxsize=1)
def get_settings() -> PlanWorkerSettings:
    """設定のシングルトンインスタンスを取得"""
    return PlanWorkerSettings()


# シングルトンインスタンス
settings = get_settings()

__all__ = ["settings", "PlanWorkerSettings", "get_settings"]
