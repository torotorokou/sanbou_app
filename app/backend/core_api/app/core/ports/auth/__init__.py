"""
Auth Ports - 認証ポート定義

【概要】
認証プロバイダの抽象インターフェースを定義します。

【主なインターフェース】
- IAuthProvider: 認証プロバイダの抽象基底クラス
"""

from .auth_provider import IAuthProvider

__all__ = ["IAuthProvider"]
