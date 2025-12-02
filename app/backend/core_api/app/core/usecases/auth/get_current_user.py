"""
Get Current User UseCase - 現在ユーザー取得ユースケース

【概要】
現在ログインしているユーザー情報を取得するユースケース。

【責務】
- IAuthProvider に委譲してユーザー情報を取得
- 認証方式の詳細は抽象化され、UseCase は関知しない

【設計方針】
- Clean Architecture の UseCase 層
- ドメインロジックとインフラストラクチャの橋渡し
- 認証プロバイダの切り替えは DI で制御
"""

from fastapi import Request
from app.core.domain.auth.entities import AuthUser
from app.core.ports.auth.auth_provider import IAuthProvider


class GetCurrentUserUseCase:
    """
    現在ユーザー取得ユースケース
    
    認証プロバイダに委譲して、現在のリクエストから
    ログイン済みユーザー情報を取得します。
    
    Attributes:
        _auth_provider: 認証プロバイダ（Dev / IAP / OAuth2）
    
    Examples:
        >>> provider = DevAuthProvider()
        >>> usecase = GetCurrentUserUseCase(provider)
        >>> user = await usecase.execute(request)
        >>> user.email
        'dev-user@honest-recycle.co.jp'
    """
    
    def __init__(self, auth_provider: IAuthProvider) -> None:
        """
        ユースケースを初期化
        
        Args:
            auth_provider: 認証プロバイダ実装（DI で注入される）
        """
        self._auth_provider = auth_provider
    
    async def execute(self, request: Request) -> AuthUser:
        """
        現在のユーザー情報を取得
        
        Args:
            request: FastAPI Request オブジェクト
            
        Returns:
            AuthUser: 認証済みユーザー情報
            
        Raises:
            HTTPException: 認証失敗時（401 / 403）
        
        Note:
            実際の認証処理は auth_provider に委譲されます。
            認証方式（Dev / IAP / OAuth2）の切り替えは DI で制御します。
        """
        return await self._auth_provider.get_current_user(request)
