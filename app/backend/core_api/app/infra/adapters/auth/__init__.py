"""
Auth Adapters - 認証アダプター

【概要】
認証プロバイダの具体的な実装を提供します。

【実装クラス】
- DevAuthProvider: 開発用固定ユーザー
- IapAuthProvider: Google Cloud IAP 統合
"""

from .dev_auth_provider import DevAuthProvider
from .iap_auth_provider import IapAuthProvider

__all__ = ["DevAuthProvider", "IapAuthProvider"]
