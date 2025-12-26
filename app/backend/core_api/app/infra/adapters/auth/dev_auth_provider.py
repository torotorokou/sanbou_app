"""
Dev Auth Provider - 開発用認証プロバイダ

【概要】
開発・ステージング環境で使用する固定ユーザーを返すプロバイダ。

【使用場面】
- ローカル開発環境（local_dev, local_demo）
- テスト実行時

【環境設定】
- AUTH_MODE=dummy
- 使用環境: local_dev, local_demo

【設計方針】
- 認証チェックなしで常に固定ユーザーを返す
- 本番環境では使用しない（環境変数で切り替え）
- deps.py の get_auth_provider() で STAGE=prod の場合は使用不可

【セキュリティ要件】
⚠️ 本番環境（STAGE=prod）では絶対に使用しないでください
   deps.py で起動時にバリデーションを実施しています
"""

import os

from fastapi import Request

from app.core.domain.auth.entities import AuthUser
from app.core.ports.auth.auth_provider import IAuthProvider
from backend_shared.application.logging import create_log_context, get_module_logger

logger = get_module_logger(__name__)


class DevAuthProvider(IAuthProvider):
    """
    開発用認証プロバイダ

    認証チェックを行わず、常に固定の開発用ユーザーを返します。
    本番環境では AUTH_MODE 環境変数を "iap" または "oauth2" に設定し、
    このプロバイダを使用しないようにしてください。

    Attributes:
        _dev_user: 固定の開発用ユーザー情報

    Examples:
        >>> provider = DevAuthProvider()
        >>> user = await provider.get_current_user(request)
        >>> user.email
        'dev-user@honest-recycle.co.jp'
    """

    def __init__(self) -> None:
        """
        開発用プロバイダを初期化

        環境変数からユーザー情報を読み込みます。
        未設定の場合はデフォルト値を使用します。

        Environment Variables:
            DEV_USER_EMAIL: 開発ユーザーのメールアドレス
            DEV_USER_NAME: 開発ユーザーの表示名
            DEV_USER_ID: 開発ユーザーのID
            DEV_USER_ROLE: 開発ユーザーのロール
        """
        dev_email = os.getenv("DEV_USER_EMAIL", "dev-user@honest-recycle.co.jp")
        dev_name = os.getenv("DEV_USER_NAME", "開発ユーザー")
        dev_id = os.getenv("DEV_USER_ID", "dev_001")
        dev_role = os.getenv("DEV_USER_ROLE", "admin")

        self._dev_user = AuthUser(
            email=dev_email,
            display_name=dev_name,
            user_id=dev_id,
            role=dev_role,
        )
        logger.info(
            "DevAuthProvider initialized",
            extra=create_log_context(
                operation="dev_auth_init",
                user_email=self._dev_user.email,
                user_role=self._dev_user.role,
                metadata={
                    "source": "environment_variables",
                    "user_id": dev_id,
                },
            ),
        )

    async def get_current_user(self, request: Request) -> AuthUser:
        """
        固定の開発用ユーザーを返す

        Args:
            request: FastAPI Request オブジェクト（未使用）

        Returns:
            AuthUser: 固定の開発用ユーザー情報

        Note:
            本番環境では使用しないでください。
            IAP や OAuth2 による適切な認証を実装してください。
        """
        # TODO: 本番環境では AUTH_MODE を "iap" または "oauth2" に設定し、
        #       このプロバイダを使用しないようにすること
        logger.debug(
            "Returning fixed dev user",
            extra=create_log_context(
                operation="get_current_user",
                user_email=self._dev_user.email,
                user_id=self._dev_user.user_id,
            ),
        )
        return self._dev_user
