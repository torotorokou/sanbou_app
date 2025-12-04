import os
from pydantic import BaseModel, Field
from backend_shared.infra.db.url_builder import build_database_url_with_driver


def _build_database_url() -> str:
    """環境変数からDATABASE_URLを構築（SQLAlchemy用）"""
    return build_database_url_with_driver(driver="psycopg")


class Settings(BaseModel):
    database_url: str = Field(default_factory=_build_database_url)
    lookback_years: int = Field(default=int(os.getenv("LOOKBACK_YEARS", "5")))
    log_level: str = Field(default=os.getenv("LOG_LEVEL", "INFO"))

settings = Settings()
