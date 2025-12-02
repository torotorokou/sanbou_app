"""
Dev Auth Provider - 開発用認証プロバイダ

【概要】
開発・ステージング環境で使用する固定ユーザーを返すプロバイダ。

【使用場面】
- ローカル開発環境
- ステージング環境（IAP 未設定時）
- テスト実行時

【設計方針】
- 認証チェックなしで常に固定ユーザーを返す
- 本番環境では使用しない（環境変数で切り替え）
- TODO コメントで本番対応が必要なことを明示
"""

import logging
from fastapi import Request
from app.core.domain.auth.entities import AuthUser
from app.core.ports.auth.auth_provider import IAuthProvider
from backend_shared.application.logging import create_log_context

logger = logging.getLogger(__name__)


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
        
        固定ユーザー情報を設定します。
        必要に応じて環境変数からユーザー情報をカスタマイズすることも可能。
        """
        self._dev_user = AuthUser(
            email="dev-user@honest-recycle.co.jp",
            display_name="開発ユーザー",
            user_id="dev_001",
            role="admin",
        )
        logger.info(
            "DevAuthProvider initialized",
            extra=create_log_context(user_email=self._dev_user.email, user_role=self._dev_user.role)
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
            "Returning dev user",
            extra=create_log_context(user_email=self._dev_user.email, user_id=self._dev_user.user_id)
        )
        return self._dev_user
