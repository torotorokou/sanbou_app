import os
from pydantic import BaseModel, Field

class Settings(BaseModel):
    database_url: str = Field(default=os.getenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/db"))
    lookback_years: int = Field(default=int(os.getenv("LOOKBACK_YEARS", "5")))
    log_level: str = Field(default=os.getenv("LOG_LEVEL", "INFO"))

settings = Settings()
