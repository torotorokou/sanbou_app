# 共通: DSNと基本import
import os, json, math, datetime as dt
import numpy as np
import pandas as pd
import psycopg

def _dsn() -> str:
    dsn = os.getenv("DATABASE_URL") or os.getenv("DB_DSN")
    if dsn: return dsn.strip()
    host = os.getenv("DB_HOST", os.getenv("POSTGRES_HOST","db"))
    port = os.getenv("DB_PORT", os.getenv("POSTGRES_PORT","5432"))
    user = os.getenv("DB_USER", os.getenv("POSTGRES_USER","myuser"))
    pw   = os.getenv("DB_PASSWORD", os.getenv("POSTGRES_PASSWORD","mypassword"))
    db   = os.getenv("DB_NAME", os.getenv("POSTGRES_DB","sanbou_dev"))
    return f"postgresql://{user}:{pw}@{host}:{port}/{db}"
