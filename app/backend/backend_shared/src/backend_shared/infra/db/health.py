"""
Database health check utility.

Provides PostgreSQL database connection health check functionality.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

try:
    import psycopg
    PSYCOPG_AVAILABLE = True
except ImportError:
    PSYCOPG_AVAILABLE = False

from backend_shared.infra.db.url_builder import build_database_url


@dataclass
class DbHealth:
    """
    Database health check result.
    
    Attributes:
        ok: 接続が成功したかどうか
        latency_ms: 接続とクエリの実行にかかった時間（ミリ秒）
        version: PostgreSQLのバージョン情報
        error: エラーが発生した場合のエラーメッセージ
    """

    ok: bool
    latency_ms: float | None
    version: str | None
    error: str | None


def ping_database(
    timeout_sec: int = 2,
    database_url: Optional[str] = None,
) -> DbHealth:
    """
    PostgreSQLデータベースへの接続をテストし、ヘルスステータスを返す
    
    Args:
        timeout_sec: 接続タイムアウト（秒）（デフォルト: 2）
        database_url: 接続先URL（Noneの場合は環境変数から自動構築）
        
    Returns:
        DbHealth: 接続結果を含むヘルスチェックオブジェクト
        
    Raises:
        ImportError: psycopg3 がインストールされていない場合
        
    Examples:
        >>> health = ping_database()
        >>> if health.ok:
        ...     print(f"DB is healthy (latency: {health.latency_ms:.2f}ms)")
        ... else:
        ...     print(f"DB is unhealthy: {health.error}")
    """
    if not PSYCOPG_AVAILABLE:
        return DbHealth(
            ok=False,
            latency_ms=None,
            version=None,
            error="psycopg3 is not installed. Install it with: pip install psycopg[binary]",
        )
    
    # DATABASE_URL の構築
    if database_url is None:
        try:
            database_url = build_database_url(driver=None, raise_on_missing=True)
        except ValueError as e:
            return DbHealth(
                ok=False,
                latency_ms=None,
                version=None,
                error=f"Database URL construction failed: {e}",
            )
    
    # データベース接続テスト
    t0 = time.time()
    try:
        with psycopg.connect(database_url, connect_timeout=timeout_sec) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                row = cur.fetchone()
                ver = row[0] if row else "unknown"
        
        ms = (time.time() - t0) * 1000.0
        return DbHealth(
            ok=True,
            latency_ms=ms,
            version=str(ver),
            error=None,
        )
    except Exception as e:
        return DbHealth(
            ok=False,
            latency_ms=None,
            version=None,
            error=f"{type(e).__name__}: {e}",
        )


def check_database_connection(timeout_sec: int = 2) -> bool:
    """
    データベース接続が可能かどうかを真偽値で返す
    
    シンプルなヘルスチェック用のヘルパー関数。
    詳細情報が必要な場合は ping_database() を使用してください。
    
    Args:
        timeout_sec: 接続タイムアウト（秒）
        
    Returns:
        bool: 接続成功時は True、失敗時は False
        
    Examples:
        >>> if check_database_connection():
        ...     print("Database is accessible")
        ... else:
        ...     print("Database connection failed")
    """
    health = ping_database(timeout_sec=timeout_sec)
    return health.ok
