"""Database health check utility."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass

import psycopg


@dataclass
class DbHealth:
    """Database health check result."""

    ok: bool
    latency_ms: float | None
    version: str | None
    error: str | None


def _dsn() -> str:
    """Build DSN from environment variables."""
    dsn = os.getenv("DATABASE_URL")
    if dsn and dsn.strip():
        return dsn.strip()
    
    # DATABASE_URL が未設定の場合、POSTGRES_* 環境変数から構築
    host = os.getenv("DB_HOST") or os.getenv("POSTGRES_HOST", "db")
    port = os.getenv("DB_PORT") or os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("DB_USER") or os.getenv("POSTGRES_USER", "")
    pwd = os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD", "")
    name = os.getenv("DB_NAME") or os.getenv("POSTGRES_DB", "")
    
    if not user or not pwd or not name:
        raise ValueError(
            "DATABASE_URL is not set and DB_USER/POSTGRES_USER, DB_PASSWORD/POSTGRES_PASSWORD, "
            "or DB_NAME/POSTGRES_DB is missing. Please set DATABASE_URL or all required environment variables."
        )
    
    return f"postgresql://{user}:{pwd}@{host}:{port}/{name}"


def ping_db(timeout_sec: int = 2) -> DbHealth:
    """
    Ping database and return health status.

    Args:
        timeout_sec: Connection timeout in seconds (default: 2)

    Returns:
        DbHealth object with connection result
    """
    t0 = time.time()
    try:
        with psycopg.connect(_dsn(), connect_timeout=timeout_sec) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                row = cur.fetchone()
                ver = row[0] if row else "unknown"
        ms = (time.time() - t0) * 1000.0
        return DbHealth(ok=True, latency_ms=ms, version=str(ver), error=None)
    except Exception as e:
        return DbHealth(
            ok=False, latency_ms=None, version=None, error=f"{type(e).__name__}: {e}"
        )
