"""
Database Connection Mode - app_user と migrator の分離管理

【概要】
将来的なDB接続ユーザーの分離（アプリ実行用 / マイグレーション用）を
可能にするための基盤モジュール。

【設計方針】
- 現在は app_user のみで動作
- migrator 用の環境変数が設定されている場合はそちらを使用
- 未設定の場合は app_user にフォールバック（後方互換性）

【使用例】
```python
from backend_shared.infra.db import get_db_url

# 通常のアプリ接続
app_url = get_db_url(mode="app")

# マイグレーション接続（未設定ならappにフォールバック）
migrator_url = get_db_url(mode="migrator")
```
"""

from __future__ import annotations

import os
from enum import Enum
from typing import Literal


class DBConnectionMode(str, Enum):
    """
    DB接続モード

    Attributes:
        APP: 通常のアプリケーション実行用接続
        MIGRATOR: DDL操作を含むマイグレーション用接続
    """

    APP = "app"
    MIGRATOR = "migrator"


def get_db_connection_params(
    mode: Literal["app", "migrator"] = "app",
) -> dict[str, str]:
    """
    接続モードに応じたDB接続パラメータを取得

    Args:
        mode: 接続モード ("app" or "migrator")

    Returns:
        dict[str, str]: DB接続パラメータ
            - user: DBユーザー名
            - password: DBパスワード
            - host: DBホスト
            - port: DBポート
            - database: DB名

    Raises:
        ValueError: 必須の環境変数が未設定の場合

    Notes:
        - mode="app": DB_USER / DB_PASSWORD を優先、未設定なら POSTGRES_* を使用
        - mode="migrator": DB_MIGRATOR_USER / DB_MIGRATOR_PASSWORD を優先、
                          未設定なら app モードにフォールバック
        - DATABASE_URL が設定されている場合はパースして使用（将来実装）

    Examples:
        >>> os.environ["DB_USER"] = "app_user"
        >>> os.environ["DB_PASSWORD"] = "app_pass"
        >>> params = get_db_connection_params(mode="app")
        >>> params["user"]
        'app_user'

        >>> # migrator未設定時はappにフォールバック
        >>> params = get_db_connection_params(mode="migrator")
        >>> params["user"]
        'app_user'
    """
    # DATABASE_URL が設定されている場合の処理（今後の拡張ポイント）
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # TODO: DATABASE_URL をパースして返す（将来実装）
        # 現在は env からの構築のみをサポート
        pass

    # mode に応じた環境変数の取得
    if mode == "migrator":
        # migrator用の環境変数を優先取得
        user = os.getenv("DB_MIGRATOR_USER") or os.getenv("DB_USER")
        password = os.getenv("DB_MIGRATOR_PASSWORD") or os.getenv("DB_PASSWORD")

        # 未設定の場合は POSTGRES_* にフォールバック
        if not user:
            user = os.getenv("POSTGRES_USER", "")
        if not password:
            password = os.getenv("POSTGRES_PASSWORD", "")
    else:
        # app用の環境変数を取得
        user = os.getenv("DB_USER") or os.getenv("POSTGRES_USER", "")
        password = os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD", "")

    # 共通パラメータ
    host = os.getenv("DB_HOST") or os.getenv("POSTGRES_HOST", "db")
    port = os.getenv("DB_PORT") or os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("DB_NAME") or os.getenv("POSTGRES_DB", "")

    # 必須パラメータの検証
    missing_params = []
    if not user:
        missing_params.append("DB_USER (or POSTGRES_USER)")
    if not password:
        missing_params.append("DB_PASSWORD (or POSTGRES_PASSWORD)")
    if not database:
        missing_params.append("DB_NAME (or POSTGRES_DB)")

    if missing_params:
        raise ValueError(
            f"Required environment variables are missing for mode='{mode}': "
            f"{', '.join(missing_params)}. "
            f"Please set these in your .env file."
        )

    return {
        "user": user,
        "password": password,
        "host": host,
        "port": port,
        "database": database,
    }
