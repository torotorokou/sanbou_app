"""
CORS Configuration - CORS設定ユーティリティ

【概要】
FastAPIアプリケーションに統一されたCORS設定を提供します。
環境変数でオリジンを設定可能で、セキュリティベストプラクティスに従います。

【主な機能】
1. 環境変数からCORS許可オリジンを取得
2. FastAPIアプリケーションへのCORSミドルウェア設定

【設計方針】
- 本番環境では必ず明示的なオリジンリストを指定
- デフォルトはローカル開発用（localhost:5173）
- セキュリティリスクのある ["*"] は推奨しない

【使用例】
```python
from backend_shared.infra.frameworks.cors_config import setup_cors
from fastapi import FastAPI

app = FastAPI()
setup_cors(app)  # 環境変数から自動取得
```
"""

import os

from backend_shared.application.logging import get_module_logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = get_module_logger(__name__)


def get_cors_origins() -> list[str]:
    """
    CORS許可オリジンのリストを環境変数から取得

    環境変数 CORS_ORIGINS をカンマ区切りで読み込みます。
    未設定の場合はローカル開発用のデフォルト値を返します。

    セキュリティ上の理由から、本番環境では必ず明示的なオリジンリストを設定してください。
    ワイルドカード ["*"] は避けるべきです。

    Returns:
        list[str]: CORS許可オリジンのリスト

    Examples:
        >>> os.environ["CORS_ORIGINS"] = "http://example.com,http://localhost:3000"
        >>> get_cors_origins()
        ['http://example.com', 'http://localhost:3000']

        >>> # 空白は自動的にトリムされる
        >>> os.environ["CORS_ORIGINS"] = "http://example.com , http://localhost:3000 "
        >>> get_cors_origins()
        ['http://example.com', 'http://localhost:3000']

        >>> # 環境変数未設定の場合はデフォルト値
        >>> os.environ.pop("CORS_ORIGINS", None)
        >>> get_cors_origins()
        ['http://localhost:5173', 'http://127.0.0.1:5173']
    """
    default_origins = "http://localhost:5173,http://127.0.0.1:5173"
    origins_str = os.getenv("CORS_ORIGINS", default_origins)
    origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]

    # セキュリティ警告: ワイルドカードが使用されている場合
    if "*" in origins:
        stage = os.getenv("STAGE", "dev").lower()
        if stage in {"stg", "prod"}:
            logger.warning(
                "CORS wildcard (*) is not recommended in production environments",
                extra={
                    "operation": "cors_setup",
                    "stage": stage,
                    "security_risk": "high",
                },
            )

    return origins


def setup_cors(
    app: FastAPI,
    origins: list[str] | None = None,
    allow_credentials: bool = True,
    allow_methods: list[str] | None = None,
    allow_headers: list[str] | None = None,
) -> None:
    """
    FastAPIアプリケーションにCORSミドルウェアを設定

    Args:
        app: FastAPIアプリケーションインスタンス
        origins: 許可するオリジンのリスト（Noneの場合は環境変数から取得）
        allow_credentials: クレデンシャル（Cookie等）を許可するか
        allow_methods: 許可するHTTPメソッドのリスト（Noneの場合は全て許可）
        allow_headers: 許可するHTTPヘッダーのリスト（Noneの場合は全て許可）

    Examples:
        >>> from fastapi import FastAPI
        >>> app = FastAPI()
        >>>
        >>> # 環境変数から自動取得
        >>> setup_cors(app)
        >>>
        >>> # 明示的にオリジンを指定
        >>> setup_cors(app, origins=["http://example.com"])
        >>>
        >>> # クレデンシャルを無効化
        >>> setup_cors(app, allow_credentials=False)
        >>>
        >>> # 特定のメソッドのみ許可
        >>> setup_cors(app, allow_methods=["GET", "POST"])

    Note:
        - allow_credentials=True の場合、origins に "*" は使用できません
        - 本番環境では必ず明示的なオリジンリストを指定してください
        - クレデンシャルが必要ない場合は allow_credentials=False にしてください
    """
    if origins is None:
        origins = get_cors_origins()

    if allow_methods is None:
        allow_methods = ["*"]

    if allow_headers is None:
        allow_headers = ["*"]

    # CORSミドルウェアを追加
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=allow_credentials,
        allow_methods=allow_methods,
        allow_headers=allow_headers,
    )

    logger.info(
        "CORS middleware configured",
        extra={
            "operation": "cors_setup",
            "origins_count": len(origins),
            "allow_credentials": allow_credentials,
            "origins": (
                origins
                if len(origins) <= 5
                else f"{origins[:5]}... (total: {len(origins)})"
            ),
        },
    )


__all__ = [
    "get_cors_origins",
    "setup_cors",
]
