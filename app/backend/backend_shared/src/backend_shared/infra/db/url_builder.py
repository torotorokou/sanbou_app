"""
Database URL builder utility.

Provides functions to construct PostgreSQL database URLs from environment variables
or explicit parameters.
"""

from __future__ import annotations
import os
from urllib.parse import quote_plus


def build_postgres_dsn(
    *,
    user: str,
    password: str,
    host: str,
    port: int | str,
    database: str,
    driver: str = "psycopg",
) -> str:
    """
    PostgreSQL用のSQLAlchemy DSNを安全に構築する共通関数
    
    ユーザー名とパスワードをURLエンコードするため、特殊文字（/, @, :など）が
    含まれていても安全に接続できます。
    
    Args:
        user: データベースユーザー名
        password: データベースパスワード（特殊文字を含んでもOK）
        host: データベースホスト名またはIPアドレス
        port: ポート番号（int または str）
        database: データベース名
        driver: SQLAlchemyドライバー名（デフォルト: "psycopg"）
                psycopg, asyncpg, psycopg2 など
    
    Returns:
        str: SQLAlchemy用のDSN文字列
        
    Examples:
        >>> # 通常のパスワード
        >>> build_postgres_dsn(
        ...     user="myuser",
        ...     password="mypass",
        ...     host="localhost",
        ...     port=5432,
        ...     database="mydb",
        ...     driver="psycopg"
        ... )
        'postgresql+psycopg://myuser:mypass@localhost:5432/mydb'
        
        >>> # 特殊文字を含むパスワード
        >>> build_postgres_dsn(
        ...     user="app_user",
        ...     password="p@ss/w:rd",
        ...     host="db.example.com",
        ...     port=5432,
        ...     database="production",
        ...     driver="asyncpg"
        ... )
        'postgresql+asyncpg://app_user:p%40ss%2Fw%3Ard@db.example.com:5432/production'
    
    Notes:
        - この関数はインフラ層（DB接続管理）専用です
        - ドメイン層やアプリケーション層から直接呼び出さないでください
        - 環境変数から構築する場合は build_database_url() を使用してください
    """
    safe_user = quote_plus(user)
    safe_password = quote_plus(password)
    return f"postgresql+{driver}://{safe_user}:{safe_password}@{host}:{port}/{database}"


def build_database_url(
    driver: str | None = None,
    raise_on_missing: bool = True,
) -> str:
    """
    環境変数からデータベース接続URLを構築
    
    優先順位:
    1. DATABASE_URL 環境変数（そのまま使用）
    2. POSTGRES_* 環境変数から動的構築
    3. エラー or 空文字列（raise_on_missing による）
    
    Args:
        driver: SQLAlchemyドライバー指定 (例: "psycopg", "psycopg2")
                None の場合は "postgresql://" のまま
        raise_on_missing: 必須環境変数が未設定の場合にエラーを発生させるか
        
    Returns:
        str: データベース接続URL
        
    Raises:
        ValueError: raise_on_missing=True で必須環境変数が未設定の場合
        
    Examples:
        >>> # DATABASE_URL が設定されている場合
        >>> os.environ["DATABASE_URL"] = "postgresql://user:pass@host:5432/db"
        >>> build_database_url()
        'postgresql://user:pass@host:5432/db'
        
        >>> # POSTGRES_* 環境変数から構築
        >>> os.environ.pop("DATABASE_URL", None)
        >>> os.environ["POSTGRES_USER"] = "myuser"
        >>> os.environ["POSTGRES_PASSWORD"] = "mypass"
        >>> os.environ["POSTGRES_DB"] = "mydb"
        >>> build_database_url()
        'postgresql://myuser:mypass@db:5432/mydb'
        
        >>> # SQLAlchemy driver 指定
        >>> build_database_url(driver="psycopg")
        'postgresql+psycopg://myuser:mypass@db:5432/mydb'
    """
    # 1. DATABASE_URL が設定されていればそのまま使用
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        url = database_url.strip()
        if driver:
            # driver 指定がある場合は postgresql:// を置換
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", f"postgresql+{driver}://", 1)
        return url
    
    # 2. POSTGRES_* 環境変数から構築
    user = os.getenv("POSTGRES_USER", "")
    password = os.getenv("POSTGRES_PASSWORD", "")
    host = os.getenv("POSTGRES_HOST", "db")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "")
    
    # 3. 必須変数のチェック
    if not user or not password or not database:
        if raise_on_missing:
            raise ValueError(
                "DATABASE_URL is not set and POSTGRES_USER, POSTGRES_PASSWORD, "
                "or POSTGRES_DB is missing. Please set DATABASE_URL or all "
                "required POSTGRES_* environment variables."
            )
        return ""
    
    # 4. build_postgres_dsn を使用してURL構築（URLエンコード含む）
    if driver:
        return build_postgres_dsn(
            user=user,
            password=password,
            host=host,
            port=port,
            database=database,
            driver=driver,
        )
    else:
        # driver 指定なしの場合は "postgresql://" のみ
        safe_user = quote_plus(user)
        safe_password = quote_plus(password)
        return f"postgresql://{safe_user}:{safe_password}@{host}:{port}/{database}"


def build_database_url_with_driver(driver: str = "psycopg") -> str:
    """
    SQLAlchemyドライバー指定でデータベースURLを構築
    
    SQLAlchemy 2.x で推奨される形式（postgresql+psycopg://）を生成。
    
    Args:
        driver: SQLAlchemyドライバー名（デフォルト: "psycopg"）
                
    Returns:
        str: ドライバー指定付きデータベース接続URL
        
    Examples:
        >>> build_database_url_with_driver()
        'postgresql+psycopg://user:pass@host:5432/db'
        
        >>> build_database_url_with_driver(driver="psycopg2")
        'postgresql+psycopg2://user:pass@host:5432/db'
    """
    return build_database_url(driver=driver, raise_on_missing=True)
