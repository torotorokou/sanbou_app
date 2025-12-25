"""
環境変数ユーティリティ - 環境変数読み込みの共通化

【概要】
すべてのバックエンドサービスで使用する環境変数の読み込みロジックを提供します。
型安全性、デフォルト値、バリデーションを統一的に扱います。

【主な機能】
1. 真偽値の統一的な解釈 (true/false/1/0/yes/no)
2. 環境判定（dev/stg/prod）
3. DEBUG/IAP設定の統一的な取得
4. API URLの取得

【設計方針】
- DRY原則: 環境変数読み込みロジックの重複を排除
- 型安全性: 明確な型注釈とバリデーション
- 柔軟性: デフォルト値のカスタマイズ可能
- 一貫性: 全サービスで同じロジックを使用

【使用例】
```python
from backend_shared.config.env_utils import (
    get_bool_env,
    is_debug_mode,
    is_iap_enabled,
    get_iap_audience,
    get_stage,
)

# DEBUG モード判定
if is_debug_mode():
    print("Debug mode enabled")

# IAP 設定取得
if is_iap_enabled():
    audience = get_iap_audience()
    print(f"IAP enabled with audience: {audience}")

# 環境判定
if get_stage() == "prod":
    print("Production environment")
```
"""

import os
from typing import Optional


def get_bool_env(key: str, default: bool = False) -> bool:
    """
    環境変数を真偽値として取得

    true/false/1/0/yes/no を統一的に解釈します（大文字小文字不問）。

    Args:
        key: 環境変数名
        default: 環境変数が未設定の場合のデフォルト値

    Returns:
        bool: 環境変数の真偽値

    Examples:
        >>> os.environ["DEBUG"] = "true"
        >>> get_bool_env("DEBUG")
        True
        >>> os.environ["DEBUG"] = "1"
        >>> get_bool_env("DEBUG")
        True
        >>> os.environ["DEBUG"] = "false"
        >>> get_bool_env("DEBUG")
        False
        >>> get_bool_env("MISSING_VAR", default=True)
        True
    """
    value = os.getenv(key, "").lower()
    if not value:
        return default
    return value in ("true", "1", "yes", "on")


def get_int_env(key: str, default: int = 0) -> int:
    """
    環境変数を整数として取得

    Args:
        key: 環境変数名
        default: 環境変数が未設定または変換失敗の場合のデフォルト値

    Returns:
        int: 環境変数の整数値

    Examples:
        >>> os.environ["PORT"] = "8080"
        >>> get_int_env("PORT")
        8080
        >>> get_int_env("MISSING_PORT", default=3000)
        3000
    """
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_str_env(key: str, default: str = "") -> str:
    """
    環境変数を文字列として取得

    Args:
        key: 環境変数名
        default: 環境変数が未設定の場合のデフォルト値

    Returns:
        str: 環境変数の文字列値

    Examples:
        >>> os.environ["API_KEY"] = "secret123"
        >>> get_str_env("API_KEY")
        'secret123'
        >>> get_str_env("MISSING_KEY", default="default_value")
        'default_value'
    """
    return os.getenv(key, default)


# ========================================
# 共通環境変数の便利関数
# ========================================


def is_debug_mode() -> bool:
    """
    DEBUG モードが有効かどうかを判定

    環境変数 DEBUG の値を統一的に解釈します。

    Returns:
        bool: DEBUG=true/1/yes の場合 True

    Examples:
        >>> os.environ["DEBUG"] = "true"
        >>> is_debug_mode()
        True
        >>> os.environ["DEBUG"] = "false"
        >>> is_debug_mode()
        False
    """
    return get_bool_env("DEBUG", default=False)


def is_iap_enabled() -> bool:
    """
    IAP（Identity-Aware Proxy）が有効かどうかを判定

    環境変数 IAP_ENABLED の値を統一的に解釈します。

    Returns:
        bool: IAP_ENABLED=true/1/yes の場合 True

    Examples:
        >>> os.environ["IAP_ENABLED"] = "true"
        >>> is_iap_enabled()
        True
        >>> os.environ["IAP_ENABLED"] = "false"
        >>> is_iap_enabled()
        False
    """
    return get_bool_env("IAP_ENABLED", default=False)


def get_iap_audience() -> Optional[str]:
    """
    IAP の audience 値を取得

    JWT 検証に必要な audience 値を環境変数から取得します。
    形式: /projects/PROJECT_NUMBER/global/backendServices/SERVICE_ID

    Returns:
        Optional[str]: IAP_AUDIENCE の値、未設定の場合は None

    Examples:
        >>> os.environ["IAP_AUDIENCE"] = "/projects/123/global/backendServices/456"
        >>> get_iap_audience()
        '/projects/123/global/backendServices/456'
    """
    audience = get_str_env("IAP_AUDIENCE")
    return audience if audience else None


def get_stage() -> str:
    """
    実行環境ステージを取得

    環境変数 STAGE または APP_ENV から環境を判定します。
    優先順位: STAGE > APP_ENV > デフォルト("dev")

    Returns:
        str: 環境ステージ ("dev", "stg", "prod", "demo" など)

    Examples:
        >>> os.environ["STAGE"] = "prod"
        >>> get_stage()
        'prod'
        >>> os.environ.pop("STAGE", None)
        >>> os.environ["APP_ENV"] = "stg"
        >>> get_stage()
        'stg'
    """
    return get_str_env("STAGE") or get_str_env("APP_ENV", default="dev")


def is_production() -> bool:
    """
    本番環境かどうかを判定

    Returns:
        bool: STAGE または APP_ENV が "prod" の場合 True

    Examples:
        >>> os.environ["STAGE"] = "prod"
        >>> is_production()
        True
        >>> os.environ["STAGE"] = "dev"
        >>> is_production()
        False
    """
    return get_stage() == "prod"


def is_development() -> bool:
    """
    開発環境かどうかを判定

    Returns:
        bool: STAGE または APP_ENV が "dev" の場合 True

    Examples:
        >>> os.environ["STAGE"] = "dev"
        >>> is_development()
        True
        >>> os.environ["STAGE"] = "prod"
        >>> is_development()
        False
    """
    return get_stage() == "dev"


# ========================================
# API URL 取得
# ========================================


def get_api_base_url(service_name: str, default_port: int = 8000) -> str:
    """
    内部マイクロサービスのベースURLを取得

    環境変数 {SERVICE_NAME}_API_BASE が設定されていない場合、
    Docker Compose のサービス名とデフォルトポートから構築します。

    Args:
        service_name: サービス名 ("rag", "ledger", "manual", "ai" など)
        default_port: デフォルトポート（環境変数未設定時）

    Returns:
        str: APIベースURL

    Examples:
        >>> os.environ["RAG_API_BASE"] = "http://rag_api:8000"
        >>> get_api_base_url("rag")
        'http://rag_api:8000'
        >>> os.environ.pop("LEDGER_API_BASE", None)
        >>> get_api_base_url("ledger", default_port=8002)
        'http://ledger_api:8002'
    """
    env_key = f"{service_name.upper()}_API_BASE"
    default_url = f"http://{service_name.lower()}_api:{default_port}"
    return get_str_env(env_key, default=default_url)


def get_database_url(default: str | None = None) -> str:
    """
    データベース接続URLを取得

    環境変数 DATABASE_URL が設定されていない場合は、
    POSTGRES_* 環境変数から動的に構築します。

    Note:
        この関数は backend_shared.infra.db.url_builder.build_database_url() の
        ラッパーです。新しいコードでは直接 build_database_url() を使用してください。

    Args:
        default: デフォルトのデータベースURL（非推奨：環境変数を使用してください）

    Returns:
        str: データベース接続URL

    Examples:
        >>> os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/mydb"
        >>> get_database_url()
        'postgresql://user:pass@localhost:5432/mydb'
    """
    from backend_shared.infra.db.url_builder import build_database_url

    try:
        return build_database_url(driver=None, raise_on_missing=True)
    except ValueError:
        if default:
            return default
        raise


def get_log_level(default: str = "INFO") -> str:
    """
    ログレベルを取得

    Args:
        default: デフォルトのログレベル

    Returns:
        str: ログレベル ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

    Examples:
        >>> os.environ["LOG_LEVEL"] = "DEBUG"
        >>> get_log_level()
        'DEBUG'
        >>> get_log_level(default="WARNING")
        'WARNING'
    """
    return get_str_env("LOG_LEVEL", default=default).upper()


def get_default_auth_excluded_paths() -> list[str]:
    """
    認証除外パスのデフォルトリストを取得

    全サービスで共通の認証除外パスを返します。
    各サービスで追加のパスを除外したい場合は、このリストに追加してください。

    Returns:
        list[str]: 認証を除外するパスのリスト

    Examples:
        >>> paths = get_default_auth_excluded_paths()
        >>> "/health" in paths
        True
        >>> "/api/healthz" in paths
        True
    """
    return [
        "/health",
        "/healthz",
        "/api/healthz",
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
    ]
