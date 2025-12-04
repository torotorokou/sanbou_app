import os
from pydantic import BaseModel, Field


def _build_database_url() -> str:
    """環境変数からDATABASE_URLを構築"""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url.strip()
    
    # DATABASE_URL が未設定の場合、POSTGRES_* 環境変数から構築
    user = os.getenv("POSTGRES_USER", "")
    password = os.getenv("POSTGRES_PASSWORD", "")
    host = os.getenv("POSTGRES_HOST", "db")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "")
    
    if not user or not password or not database:
        raise ValueError(
            "DATABASE_URL is not set and POSTGRES_USER, POSTGRES_PASSWORD, or POSTGRES_DB is missing. "
            "Please set DATABASE_URL or all required POSTGRES_* environment variables."
        )
    
    # plan_worker では postgresql+psycopg:// 形式を使用
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}"


class Settings(BaseModel):
    database_url: str = Field(default_factory=_build_database_url)
    lookback_years: int = Field(default=int(os.getenv("LOOKBACK_YEARS", "5")))
    log_level: str = Field(default=os.getenv("LOG_LEVEL", "INFO"))

settings = Settings()
