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
    mode: str = "app",
) -> str:
    """
    環境変数からデータベース接続URLを構築
    
    優先順位:
    1. DATABASE_URL 環境変数（そのまま使用）
    2. DB_USER / DB_PASSWORD 環境変数から構築（推奨）
    3. POSTGRES_* 環境変数から構築（後方互換性）
    4. エラー or 空文字列（raise_on_missing による）
    
    Args:
        driver: SQLAlchemyドライバー指定 (例: "psycopg", "psycopg2")
                None の場合は "postgresql://" のまま
        raise_on_missing: 必須環境変数が未設定の場合にエラーを発生させるか
        mode: 接続モード ("app" or "migrator")
              - "app": DB_USER / DB_PASSWORD を優先
              - "migrator": DB_MIGRATOR_USER / DB_MIGRATOR_PASSWORD を優先
                           未設定なら app にフォールバック
        
    Returns:
        str: データベース接続URL
        
    Raises:
        ValueError: raise_on_missing=True で必須環境変数が未設定の場合
        
    Examples:
        >>> # DATABASE_URL が設定されている場合
        >>> os.environ["DATABASE_URL"] = "postgresql://user:pass@host:5432/db"
        >>> build_database_url()
        'postgresql://user:pass@host:5432/db'
        
        >>> # DB_USER / DB_PASSWORD から構築（推奨）
        >>> os.environ.pop("DATABASE_URL", None)
        >>> os.environ["DB_USER"] = "app_user"
        >>> os.environ["DB_PASSWORD"] = "app_pass"
        >>> os.environ["DB_NAME"] = "mydb"
        >>> build_database_url()
        'postgresql://app_user:app_pass@db:5432/mydb'
        
        >>> # SQLAlchemy driver 指定
        >>> build_database_url(driver="psycopg")
        'postgresql+psycopg://app_user:app_pass@db:5432/mydb'
        
        >>> # migrator モード（未設定時は app にフォールバック）
        >>> build_database_url(mode="migrator")
        'postgresql://app_user:app_pass@db:5432/mydb'
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
    
    # 2. 接続パラメータの取得（connection_mode モジュール使用）
    try:
        from backend_shared.infra.db.connection_mode import get_db_connection_params
        params = get_db_connection_params(mode=mode)
        user = params["user"]
        password = params["password"]
        host = params["host"]
        port = params["port"]
        database = params["database"]
    except ImportError:
        # 後方互換性: connection_mode が利用できない場合は直接 env から取得
        if mode == "migrator":
            user = os.getenv("DB_MIGRATOR_USER") or os.getenv("DB_USER") or os.getenv("POSTGRES_USER", "")
            password = os.getenv("DB_MIGRATOR_PASSWORD") or os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD", "")
        else:
            user = os.getenv("DB_USER") or os.getenv("POSTGRES_USER", "")
            password = os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD", "")
        
        host = os.getenv("DB_HOST") or os.getenv("POSTGRES_HOST", "db")
        port = os.getenv("DB_PORT") or os.getenv("POSTGRES_PORT", "5432")
        database = os.getenv("DB_NAME") or os.getenv("POSTGRES_DB", "")
    
    # 3. 必須変数のチェック
    if not user or not password or not database:
        if raise_on_missing:
            missing = []
            if not user:
                missing.append("DB_USER or POSTGRES_USER")
            if not password:
                missing.append("DB_PASSWORD or POSTGRES_PASSWORD")
            if not database:
                missing.append("DB_NAME or POSTGRES_DB")
            
            raise ValueError(
                f"DATABASE_URL is not set and required environment variables "
                f"are missing: {', '.join(missing)}. "
                f"Please set DATABASE_URL or all required DB_* / POSTGRES_* "
                f"environment variables in your .env file."
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
