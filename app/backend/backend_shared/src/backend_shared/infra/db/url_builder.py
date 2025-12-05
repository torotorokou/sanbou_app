"""
Database URL builder utility.

Provides functions to construct PostgreSQL database URLs from environment variables.
"""

import os
from urllib.parse import quote_plus


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
    
    # 4. URL構築
    protocol = "postgresql"
    if driver:
        protocol = f"postgresql+{driver}"
    
    # ユーザー名とパスワードをURLエンコード（特殊文字対応）
    encoded_user = quote_plus(user)
    encoded_password = quote_plus(password)
    
    return f"{protocol}://{encoded_user}:{encoded_password}@{host}:{port}/{database}"


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
