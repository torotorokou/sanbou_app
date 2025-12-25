"""
Authentication Middleware - IAP 認証ミドルウェア

【概要】
全てのリクエストに対して IAP 認証を強制するミドルウェア。
ヘルスチェックエンドポイントなど、認証不要なパスは除外リストで管理。

【設計方針】
- IAP_ENABLED=true の場合のみ認証を強制
- 開発環境では DevAuthProvider を使用
- 認証失敗時は 401/403 を返す
- 除外パスは環境変数で管理可能

【使用例】
```python
from app.api.middleware.auth_middleware import AuthenticationMiddleware

app.add_middleware(
    AuthenticationMiddleware,
    excluded_paths=["/health", "/healthz", "/"]
)
```
"""

import os
from typing import List

from app.deps import get_auth_provider
from backend_shared.application.logging import get_module_logger
from backend_shared.config.env_utils import is_iap_enabled
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = get_module_logger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    IAP 認証を強制するミドルウェア

    除外パスを除く全てのリクエストで認証を実施します。

    Attributes:
        excluded_paths: 認証を除外するパスのリスト
        iap_enabled: IAP が有効かどうか
    """

    def __init__(self, app, excluded_paths: List[str] = None):
        """
        認証ミドルウェアを初期化

        Args:
            app: FastAPI アプリケーション
            excluded_paths: 認証を除外するパスのリスト
        """
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/health",
            "/healthz",
            "/api/healthz",
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]
        self.iap_enabled = is_iap_enabled()

        logger.info(
            f"AuthenticationMiddleware initialized (IAP_ENABLED={self.iap_enabled})",
            extra={
                "operation": "middleware_init",
                "iap_enabled": self.iap_enabled,
                "excluded_paths": self.excluded_paths,
            },
        )

    async def dispatch(self, request: Request, call_next):
        """
        リクエストごとに認証を実施

        Args:
            request: FastAPI Request オブジェクト
            call_next: 次のミドルウェアまたはエンドポイント

        Returns:
            Response: レスポンス
        """
        # 除外パスの場合は認証をスキップ
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # IAP が無効の場合は認証をスキップ（開発環境）
        # ただし、DevAuthProvider を使用してユーザー情報は設定する
        if not self.iap_enabled:
            # 開発環境では request.state.user に固定ユーザーを設定
            try:
                auth_provider = get_auth_provider()
                user = await auth_provider.get_current_user(request)
                request.state.user = user
            except Exception as e:
                logger.debug(
                    f"Dev auth skipped: {str(e)}",
                    extra={"operation": "dev_auth", "error": str(e)},
                )
            return await call_next(request)

        # IAP 認証を実施
        try:
            auth_provider = get_auth_provider()
            user = await auth_provider.get_current_user(request)

            # 認証成功: request.state に user を保存
            request.state.user = user

            logger.debug(
                f"Authentication successful: {user.email}",
                extra={
                    "operation": "authentication",
                    "email": user.email,
                    "user_id": user.user_id,
                },
            )

            return await call_next(request)

        except Exception as e:
            # 認証失敗
            logger.warning(
                f"Authentication failed: {str(e)}",
                extra={
                    "operation": "authentication",
                    "path": request.url.path,
                    "error": str(e),
                },
            )

            # HTTPException の場合はステータスコードを取得
            status_code = getattr(e, "status_code", 401)
            detail = getattr(e, "detail", "Authentication required")

            return JSONResponse(
                status_code=status_code,
                content={
                    "error": {
                        "code": "AUTHENTICATION_REQUIRED",
                        "message": detail,
                    }
                },
            )
