"""
IAP Auth Provider - Google Cloud IAP 認証プロバイダ

【概要】
Google Cloud Identity-Aware Proxy (IAP) が付与するヘッダーから
ユーザー情報を抽出する認証プロバイダ。

【使用場面】
- Google Cloud Run / App Engine で IAP を有効化した環境
- Load Balancer + IAP 構成の本番環境

【設計方針】
- X-Goog-Authenticated-User-Email ヘッダーを読み取り
- honest-recycle.co.jp ドメインのみを許可（ホワイトリスト方式）
- ヘッダー不在時は 401 Unauthorized を返す
- TODO コメントで本番環境での検証が必要なことを明示

【注意事項】
- IAP を有効化する前は、このプロバイダは使用できません
- 実際のヘッダー形式は IAP 有効化後に確認・微調整が必要です
- ログ出力を活用して実際のヘッダー内容を確認してください
"""

import logging
from fastapi import Request, HTTPException, status
from app.core.domain.auth.entities import AuthUser
from app.core.ports.auth.auth_provider import IAuthProvider

logger = logging.getLogger(__name__)


class IapAuthProvider(IAuthProvider):
    """
    Google Cloud IAP 認証プロバイダ
    
    IAP が付与する認証ヘッダーからユーザー情報を抽出します。
    本番環境で IAP を有効化した際に使用します。
    
    IAP Header Format:
        X-Goog-Authenticated-User-Email: accounts.google.com:user@honest-recycle.co.jp
        または
        X-Goog-Authenticated-User-Email: user@honest-recycle.co.jp
    
    Attributes:
        _allowed_domain: 許可するメールドメイン（ホワイトリスト）
    
    Examples:
        >>> provider = IapAuthProvider()
        >>> # IAP ヘッダーが存在する場合
        >>> user = await provider.get_current_user(request)
        >>> user.email
        'user@honest-recycle.co.jp'
        
        >>> # IAP ヘッダーが存在しない場合
        >>> user = await provider.get_current_user(request)
        HTTPException: 401 Unauthorized
    """
    
    def __init__(self, allowed_domain: str = "honest-recycle.co.jp") -> None:
        """
        IAP 認証プロバイダを初期化
        
        Args:
            allowed_domain: 許可するメールドメイン（デフォルト: honest-recycle.co.jp）
        """
        self._allowed_domain = allowed_domain
        logger.info(f"IapAuthProvider initialized with allowed domain: {allowed_domain}")
    
    async def get_current_user(self, request: Request) -> AuthUser:
        """
        IAP ヘッダーからユーザー情報を抽出
        
        Args:
            request: FastAPI Request オブジェクト
            
        Returns:
            AuthUser: 認証済みユーザー情報
            
        Raises:
            HTTPException: 
                - 401: IAP ヘッダーが存在しない
                - 403: 許可されていないドメインのユーザー
        
        Note:
            TODO: IAP 有効化後、実際のヘッダー形式を確認して微調整すること
            ログ出力を有効化して、ヘッダー内容を確認してください。
        """
        # TODO: IAP 有効化後、実際のヘッダー名とフォーマットを確認すること
        #       - X-Goog-Authenticated-User-Email
        #       - X-Goog-IAP-JWT-Assertion (JWT 検証が必要な場合)
        
        raw_header = request.headers.get("X-Goog-Authenticated-User-Email")
        
        if not raw_header:
            # IAP ヘッダーが存在しない場合は認証失敗
            logger.warning("IAP header not found in request")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required (IAP header not found)",
            )
        
        # ヘッダー形式を確認（開発時のデバッグ用）
        # 本番環境では個人情報ログに注意すること
        logger.debug(f"IAP header value: {raw_header}")
        
        # IAP ヘッダーの形式: "accounts.google.com:user@domain.com"
        # または単純に "user@domain.com" の場合もある
        email = raw_header
        if ":" in raw_header:
            # "accounts.google.com:user@domain.com" 形式の場合
            _, email = raw_header.split(":", 1)
        
        # ドメインチェック（ホワイトリスト方式）
        if not email.endswith(f"@{self._allowed_domain}"):
            logger.warning(f"Unauthorized domain: {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Only @{self._allowed_domain} users are allowed",
            )
        
        # 表示名はメールアドレスのローカル部分を使用
        # 例: "yamada.taro@honest-recycle.co.jp" -> "yamada.taro"
        display_name = email.split("@")[0]
        
        # TODO: 実際のユーザーIDとロールはデータベースから取得する
        # 現在は仮のIDとデフォルトロールを設定
        user_id = f"iap_{email.split('@')[0]}"
        role = "user"  # デフォルトロール
        
        logger.info(f"IAP authentication successful: {email}")
        
        return AuthUser(
            email=email,
            display_name=display_name,
            user_id=user_id,
            role=role,
        )
