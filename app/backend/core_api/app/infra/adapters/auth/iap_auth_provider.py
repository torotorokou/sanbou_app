"""
IAP Auth Provider - Google Cloud IAP 認証プロバイダ

【概要】
Google Cloud Identity-Aware Proxy (IAP) が付与するヘッダーから
ユーザー情報を抽出し、JWT署名を検証する認証プロバイダ。

【使用場面】
- Google Cloud Run / App Engine で IAP を有効化した環境
- Load Balancer + IAP 構成の本番環境

【設計方針】
- X-Goog-IAP-JWT-Assertion ヘッダーのJWT署名を検証
- honest-recycle.co.jp ドメインのみを許可（ホワイトリスト方式）
- ヘッダー不在時は 401 Unauthorized を返す
- 署名検証失敗時は 401 Unauthorized を返す

【注意事項】
- IAP を有効化する前は、このプロバイダは使用できません
- IAP_AUDIENCE 環境変数に正しい audience 値を設定してください
- audience は /projects/PROJECT_NUMBER/global/backendServices/SERVICE_ID 形式
"""

import os
from fastapi import Request, HTTPException, status
from google.auth.transport import requests
from google.oauth2 import id_token
from backend_shared.application.logging import create_log_context, get_module_logger
from app.core.domain.auth.entities import AuthUser
from app.core.ports.auth.auth_provider import IAuthProvider

logger = get_module_logger(__name__)


class IapAuthProvider(IAuthProvider):
    """
    Google Cloud IAP 認証プロバイダ
    
    IAP が付与する JWT トークンを検証してユーザー情報を抽出します。
    
    JWT Header: X-Goog-IAP-JWT-Assertion
    Email Header: X-Goog-Authenticated-User-Email (フォールバック用)
    
    Attributes:
        _allowed_domain: 許可するメールドメイン（ホワイトリスト）
        _iap_audience: IAP の audience 値（JWT 検証用）
    
    Examples:
        >>> provider = IapAuthProvider()
        >>> user = await provider.get_current_user(request)
        >>> user.email
        'user@honest-recycle.co.jp'
    """
    
    def __init__(
        self, 
        allowed_domain: str = "honest-recycle.co.jp",
        iap_audience: str | None = None
    ) -> None:
        """
        IAP 認証プロバイダを初期化
        
        Args:
            allowed_domain: 許可するメールドメイン（デフォルト: honest-recycle.co.jp）
            iap_audience: IAP の audience 値（環境変数 IAP_AUDIENCE から取得）
        """
        self._allowed_domain = allowed_domain
        self._iap_audience = iap_audience or os.getenv("IAP_AUDIENCE", "")
        
        logger.info(
            "IapAuthProvider initialized",
            extra=create_log_context(
                operation="iap_auth_init", 
                allowed_domain=allowed_domain,
                has_audience=bool(self._iap_audience)
            )
        )
    
    async def get_current_user(self, request: Request) -> AuthUser:
        """
        IAP ヘッダーからユーザー情報を抽出し、JWT 署名を検証
        
        Args:
            request: FastAPI Request オブジェクト
            
        Returns:
            AuthUser: 認証済みユーザー情報
            
        Raises:
            HTTPException: 
                - 401: IAP ヘッダーが存在しない、または JWT 検証失敗
                - 403: 許可されていないドメインのユーザー
        """
        # JWT トークンを取得
        jwt_token = request.headers.get("X-Goog-IAP-JWT-Assertion")
        
        if not jwt_token:
            # フォールバック: X-Goog-Authenticated-User-Email ヘッダーを確認
            # （開発環境やIAP設定によってはJWTが無い場合がある）
            return await self._authenticate_from_email_header(request)
        
        # JWT 署名を検証
        try:
            if not self._iap_audience:
                logger.warning(
                    "IAP_AUDIENCE not configured, skipping JWT verification",
                    extra=create_log_context(operation="get_current_user")
                )
                # audience が未設定の場合はメールヘッダーから取得
                return await self._authenticate_from_email_header(request)
            
            # JWT を検証（Google の公開鍵で署名を検証）
            decoded_token = id_token.verify_oauth2_token(
                jwt_token,
                requests.Request(),
                audience=self._iap_audience
            )
            
            # トークンから email を取得
            email = decoded_token.get("email")
            if not email:
                logger.error(
                    "Email not found in JWT token",
                    extra=create_log_context(operation="get_current_user")
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid IAP token: email not found",
                )
            
            # ドメインチェック
            if not email.endswith(f"@{self._allowed_domain}"):
                logger.warning(
                    "Unauthorized domain",
                    extra=create_log_context(
                        operation="get_current_user", 
                        email=email, 
                        allowed_domain=self._allowed_domain
                    )
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: Only @{self._allowed_domain} users are allowed",
                )
            
            # ユーザー情報を構築
            display_name = email.split("@")[0]
            user_id = decoded_token.get("sub", f"iap_{display_name}")
            
            logger.info(
                "IAP JWT authentication successful",
                extra=create_log_context(
                    operation="get_current_user", 
                    email=email, 
                    user_id=user_id
                )
            )
            
            return AuthUser(
                email=email,
                display_name=display_name,
                user_id=user_id,
                role="user",  # デフォルトロール
            )
            
        except ValueError as e:
            # JWT 検証失敗
            logger.error(
                "IAP JWT verification failed",
                extra=create_log_context(operation="get_current_user", error=str(e))
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid IAP token: {str(e)}",
            )
    
    async def _authenticate_from_email_header(self, request: Request) -> AuthUser:
        """
        X-Goog-Authenticated-User-Email ヘッダーからユーザー情報を抽出
        （JWT が利用できない場合のフォールバック）
        
        Args:
            request: FastAPI Request オブジェクト
            
        Returns:
            AuthUser: 認証済みユーザー情報
            
        Raises:
            HTTPException: ヘッダーが存在しない、または許可されていないドメイン
        """
        raw_header = request.headers.get("X-Goog-Authenticated-User-Email")
        
        if not raw_header:
            logger.warning(
                "IAP headers not found",
                extra=create_log_context(operation="get_current_user")
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required (IAP headers not found)",
            )
        
        # ヘッダー形式: "accounts.google.com:user@domain.com"
        email = raw_header
        if ":" in raw_header:
            _, email = raw_header.split(":", 1)
        
        # ドメインチェック
        if not email.endswith(f"@{self._allowed_domain}"):
            logger.warning(
                "Unauthorized domain",
                extra=create_log_context(
                    operation="get_current_user", 
                    email=email, 
                    allowed_domain=self._allowed_domain
                )
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Only @{self._allowed_domain} users are allowed",
            )
        
        display_name = email.split("@")[0]
        user_id = f"iap_{display_name}"
        
        logger.info(
            "IAP email authentication successful",
            extra=create_log_context(
                operation="get_current_user", 
                email=email, 
                user_id=user_id
            )
        )
        
        return AuthUser(
            email=email,
            display_name=display_name,
            user_id=user_id,
            role="user",
        )
