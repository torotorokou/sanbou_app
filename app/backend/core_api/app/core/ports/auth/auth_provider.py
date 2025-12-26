"""
Auth Provider Port - 認証プロバイダ抽象インターフェース

【概要】
認証方式（Dev / IAP / OAuth2 等）に依存しない抽象インターフェースを定義します。

【設計方針】
- ABC（Abstract Base Class）による抽象化
- FastAPI の Request を受け取り、AuthUser を返す単純なインターフェース
- 実装クラスは infra/adapters/auth/ に配置
"""

from abc import ABC, abstractmethod

from fastapi import Request

from app.core.domain.auth.entities import AuthUser


class IAuthProvider(ABC):
    """
    認証プロバイダの抽象インターフェース

    FastAPI の Request オブジェクトから現在のユーザー情報を取得します。
    実装クラスは認証方式（Dev / IAP / OAuth2 等）に応じて
    異なるロジックでユーザー情報を抽出します。

    Methods:
        get_current_user: 現在のリクエストから認証済みユーザーを取得

    Implementations:
        - DevAuthProvider: 開発用固定ユーザー
        - IapAuthProvider: Google Cloud IAP ヘッダー読み取り
        - (将来) OAuth2AuthProvider: 自前 OAuth2 実装
    """

    @abstractmethod
    async def get_current_user(self, request: Request) -> AuthUser:
        """
        現在のリクエストから認証済みユーザーを取得

        Args:
            request: FastAPI Request オブジェクト

        Returns:
            AuthUser: 認証済みユーザー情報

        Raises:
            HTTPException: 認証失敗時（401 Unauthorized / 403 Forbidden）
        """
        ...
