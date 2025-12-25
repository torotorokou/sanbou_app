"""
VPN Auth Provider - VPN/Tailscale 経由アクセス用認証プロバイダ

【概要】
VPN（Tailscale）経由のアクセス専用の簡易認証プロバイダ。
IAP が不要な STG 環境で使用します。

【使用場面】
- vm_stg 環境（Tailscale/VPN 経由アクセス）
- 外部に公開しない検証環境

【環境設定】
- AUTH_MODE=vpn_dummy
- 使用環境: vm_stg
- 必須環境変数:
  - VPN_USER_EMAIL: VPN ユーザーのメールアドレス
  - VPN_USER_NAME: VPN ユーザーの表示名（オプション）

【設計方針】
- 環境変数で指定された固定ユーザーを返す
- IAP ヘッダは不要（VPN 内で接続制御済み）
- 本番環境では使用しない（AUTH_MODE で切り替え）

【セキュリティ要件】
⚠️ VPN/Tailscale でのアクセス制御が前提です
   ネットワークレベルで認証済みという前提で動作します
"""

import logging
import os

from app.core.domain.auth.entities import AuthUser
from app.core.ports.auth.auth_provider import IAuthProvider
from backend_shared.application.logging import create_log_context, get_module_logger
from fastapi import Request

logger = get_module_logger(__name__)


class VpnAuthProvider(IAuthProvider):
    """
    VPN/Tailscale 経由アクセス用認証プロバイダ

    環境変数で指定された固定ユーザーを返します。
    VPN 接続制御により既に認証済みという前提で動作します。

    Attributes:
        _vpn_user: 環境変数から読み込んだ VPN ユーザー情報

    Environment Variables:
        VPN_USER_EMAIL: VPN ユーザーのメールアドレス（必須）
        VPN_USER_NAME: VPN ユーザーの表示名（オプション、デフォルト: VPN User）

    Examples:
        >>> # .env.vm_stg に以下を設定:
        >>> # AUTH_MODE=vpn_dummy
        >>> # VPN_USER_EMAIL=stg-admin@honest-recycle.co.jp
        >>> # VPN_USER_NAME=STG Administrator
        >>> provider = VpnAuthProvider()
        >>> user = await provider.get_current_user(request)
        >>> user.email
        'stg-admin@honest-recycle.co.jp'
    """

    def __init__(self) -> None:
        """
        VPN 認証プロバイダを初期化

        環境変数から VPN ユーザー情報を読み込みます。

        Raises:
            ValueError: VPN_USER_EMAIL が未設定の場合

        Environment Variables:
            VPN_USER_EMAIL: VPN ユーザーのメールアドレス（必須）
            VPN_USER_NAME: VPN ユーザーの表示名（オプション、デフォルト: VPN User）
            VPN_USER_ID: VPN ユーザーのID（オプション、デフォルト: vpn_001）
        """
        self._vpn_user_email = os.getenv("VPN_USER_EMAIL")
        if not self._vpn_user_email:
            raise ValueError(
                "VPN_USER_EMAIL environment variable is required for VPN auth mode. "
                "Please set it in secrets/.env.vm_stg.secrets"
            )

        self._vpn_user_display_name = os.getenv("VPN_USER_NAME", "VPN User")
        self._vpn_user_id = os.getenv("VPN_USER_ID", "vpn_001")

        logger.info(
            "VpnAuthProvider initialized",
            extra=create_log_context(
                operation="vpn_auth_init",
                user_email=self._vpn_user_email,
                metadata={
                    "display_name": self._vpn_user_display_name,
                    "user_id": self._vpn_user_id,
                    "source": "environment_variables",
                },
            ),
        )

    async def get_current_user(self, request: Request) -> AuthUser:
        """
        固定の VPN ユーザーを返す

        Args:
            request: FastAPI Request オブジェクト（参照のみ、検証不要）

        Returns:
            AuthUser: 環境変数で設定された VPN ユーザー

        Note:
            VPN 経由であることは nginx / firewall レベルで保証されているため、
            ここでは追加の認証チェックは行いません。
        """
        return AuthUser(
            email=self._vpn_user_email,
            display_name=self._vpn_user_display_name,
            user_id=self._vpn_user_id,
        )

    async def verify_token(self, request: Request) -> bool:
        """
        トークン検証（VPN 認証では常に True）

        Args:
            request: FastAPI Request オブジェクト

        Returns:
            bool: 常に True（VPN 接続制御により認証済み）
        """
        return True
