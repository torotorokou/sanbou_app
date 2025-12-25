"""
IAP Auth Provider - Google Cloud IAP 認証プロバイダ

【概要】
Google Cloud Identity-Aware Proxy (IAP) が付与するヘッダーから
ユーザー情報を抽出し、JWT署名を検証する認証プロバイダ。

【使用場面】
- Google Cloud Run / App Engine で IAP を有効化した環境
- Load Balancer + IAP 構成の本番環境

【環境設定】
- AUTH_MODE=iap
- 使用環境: vm_prod（本番環境）
- 必須環境変数:
  - IAP_AUDIENCE: IAP の audience 値（/projects/PROJECT_NUMBER/global/backendServices/SERVICE_ID 形式）
  - ALLOWED_EMAIL_DOMAIN: 許可するメールドメイン（デフォルト: honest-recycle.co.jp）

【設計方針】
- X-Goog-IAP-JWT-Assertion ヘッダーのJWT署名を検証（IAP公式仕様準拠）
- honest-recycle.co.jp ドメインのみを許可（ホワイトリスト方式）
- 本番環境ではJWT検証必須、ヘッダー不在時は即401
- dev環境のみ、メールヘッダーからのフォールバック認証を許可

【セキュリティ要件】
✅ 本番環境（STAGE=prod）では必須の認証プロバイダです
   deps.py で起動時に AUTH_MODE=iap と IAP_AUDIENCE の設定を強制します

【注意事項】
- IAP を有効化する前は、このプロバイダは使用できません
- IAP_AUDIENCE 環境変数に正しい audience 値を設定してください
- audience は /projects/PROJECT_NUMBER/global/backendServices/SERVICE_ID 形式
"""

from fastapi import HTTPException, Request, status
from google.auth.transport import requests
from google.oauth2 import id_token
from starlette.concurrency import run_in_threadpool

from app.core.domain.auth.entities import AuthUser
from app.core.ports.auth.auth_provider import IAuthProvider
from backend_shared.application.logging import create_log_context, get_module_logger
from backend_shared.config.env_utils import get_iap_audience, get_stage

logger = get_module_logger(__name__)


class IapAuthProvider(IAuthProvider):
    """
    Google Cloud IAP 認証プロバイダ

    IAP が付与する JWT トークンを検証してユーザー情報を抽出します。
    本番環境ではJWT検証必須、dev環境のみメールヘッダーフォールバックを許可。

    JWT Header: X-Goog-IAP-JWT-Assertion
    Email Header: X-Goog-Authenticated-User-Email (dev環境専用フォールバック)

    Attributes:
        _allowed_domain: 許可するメールドメイン（ホワイトリスト）
        _iap_audience: IAP の audience 値（JWT 検証用）

    Examples:
        >>> provider = IapAuthProvider()
        >>> user = await provider.get_current_user(request)
        >>> user.email
        'user@honest-recycle.co.jp'
    """

    # IAP JWT検証用の公式公開鍵URL
    IAP_PUBLIC_KEY_URL = "https://www.gstatic.com/iap/verify/public_key"

    def __init__(
        self,
        allowed_domain: str = "honest-recycle.co.jp",
        iap_audience: str | None = None,
    ) -> None:
        """
        IAP 認証プロバイダを初期化

        Args:
            allowed_domain: 許可するメールドメイン（デフォルト: honest-recycle.co.jp）
            iap_audience: IAP の audience 値（環境変数 IAP_AUDIENCE から取得）
        """
        self._allowed_domain = allowed_domain
        self._iap_audience = iap_audience or get_iap_audience()

        logger.info(
            "IapAuthProvider initialized",
            extra=create_log_context(
                operation="iap_auth_init",
                allowed_domain=allowed_domain,
                has_audience=bool(self._iap_audience),
            ),
        )

    async def get_current_user(self, request: Request) -> AuthUser:
        """
        IAP ヘッダーからユーザー情報を抽出し、JWT 署名を検証

        本番環境ではJWT検証必須。dev環境のみメールヘッダーフォールバックを許可。

        Args:
            request: FastAPI Request オブジェクト

        Returns:
            AuthUser: 認証済みユーザー情報

        Raises:
            HTTPException:
                - 401: IAP ヘッダーが存在しない、または JWT 検証失敗
                - 403: 許可されていないドメインのユーザー
                - 500: IAP設定エラー（IAP_AUDIENCE未設定）
        """
        # 環境判定（dev環境のみフォールバックを許可）
        env = get_stage()
        is_dev = env == "dev"

        # JWT トークンを取得
        jwt_token = request.headers.get("X-Goog-IAP-JWT-Assertion")

        if not jwt_token:
            # JWT が存在しない場合
            if is_dev:
                # dev環境: メールヘッダーからのフォールバック認証を許可
                logger.debug(
                    "JWT not found, using email header fallback (dev only)",
                    extra=create_log_context(operation="get_current_user", env=env),
                )
                return await self._authenticate_from_email_header(request)
            else:
                # 本番環境: JWT必須、即401
                logger.warning(
                    "IAP JWT header not found in non-dev environment",
                    extra=create_log_context(operation="get_current_user", env=env),
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

        # IAP_AUDIENCE 設定チェック（構成ミスは500エラー）
        if not self._iap_audience:
            logger.error(
                "IAP_AUDIENCE not configured",
                extra=create_log_context(operation="get_current_user", env=env),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="IAP configuration error",
            )

        # JWT 署名を検証（IAP公式仕様に準拠）
        try:
            # 同期I/Oをrun_in_threadpoolでラップし、イベントループをブロックしない
            decoded_token = await run_in_threadpool(
                id_token.verify_token,
                jwt_token,
                requests.Request(),
                self._iap_audience,
                certs_url=self.IAP_PUBLIC_KEY_URL,
            )

            # トークンから email と sub を取得
            email = decoded_token.get("email")
            user_id = decoded_token.get("sub")

            if not email:
                logger.error(
                    "Email not found in IAP JWT token",
                    extra=create_log_context(operation="get_current_user"),
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid IAP token",
                )

            # ドメインチェック
            if not email.endswith(f"@{self._allowed_domain}"):
                logger.warning(
                    "Unauthorized domain",
                    extra=create_log_context(
                        operation="get_current_user",
                        email=email,
                        allowed_domain=self._allowed_domain,
                    ),
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: Only @{self._allowed_domain} users are allowed",
                )

            # ユーザー情報を構築
            display_name = email.split("@")[0]
            if not user_id:
                user_id = f"iap_{display_name}"

            logger.info(
                "IAP JWT authentication successful",
                extra=create_log_context(
                    operation="get_current_user", email=email, user_id=user_id, env=env
                ),
            )

            return AuthUser(
                email=email,
                display_name=display_name,
                user_id=user_id,
                role="user",  # デフォルトロール
            )

        except ValueError as e:
            # JWT 検証失敗（詳細はログのみ、クライアントには汎用メッセージ）
            logger.error(
                "IAP JWT verification failed",
                extra=create_log_context(operation="get_current_user", error=str(e), env=env),
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid IAP token",
            )

    async def _authenticate_from_email_header(self, request: Request) -> AuthUser:
        """
        X-Goog-Authenticated-User-Email ヘッダーからユーザー情報を抽出
        （dev環境専用フォールバック。本番環境では呼ばれない）

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
                extra=create_log_context(operation="get_current_user"),
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
                    allowed_domain=self._allowed_domain,
                ),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Only @{self._allowed_domain} users are allowed",
            )

        display_name = email.split("@")[0]
        user_id = f"iap_{display_name}"

        logger.info(
            "IAP email authentication successful",
            extra=create_log_context(operation="get_current_user", email=email, user_id=user_id),
        )

        return AuthUser(
            email=email,
            display_name=display_name,
            user_id=user_id,
            role="user",
        )
