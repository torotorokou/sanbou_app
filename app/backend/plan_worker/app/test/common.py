# 共通: DSNと基本import
import os, json, math, datetime as dt
import numpy as np
import pandas as pd
import psycopg

def _dsn() -> str:
    dsn = os.getenv("DATABASE_URL") or os.getenv("DB_DSN")
    if dsn: return dsn.strip()
    
    # DATABASE_URL が未設定の場合、POSTGRES_* 環境変数から構築
    host = os.getenv("DB_HOST", os.getenv("POSTGRES_HOST","db"))
    port = os.getenv("DB_PORT", os.getenv("POSTGRES_PORT","5432"))
    user = os.getenv("DB_USER", os.getenv("POSTGRES_USER",""))
    pw   = os.getenv("DB_PASSWORD", os.getenv("POSTGRES_PASSWORD",""))
    db   = os.getenv("DB_NAME", os.getenv("POSTGRES_DB",""))
    
    if not user or not pw or not db:
        raise ValueError(
            "DATABASE_URL is not set and required credentials are missing. "
            "Please set DATABASE_URL or all POSTGRES_* environment variables."
        )
    
    return f"postgresql://{user}:{pw}@{host}:{port}/{db}"
