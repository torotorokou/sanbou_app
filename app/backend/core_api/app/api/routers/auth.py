"""
Auth Router - 認証・認可エンドポイント

【概要】
ユーザー認証情報を取得するエンドポイントを提供します。

【エンドポイント】
- GET /auth/me: 現在ログインしているユーザー情報を取得
"""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from app.core.usecases.auth.get_current_user import GetCurrentUserUseCase
from app.config.di_providers import get_get_current_user_usecase

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthMeResponse(BaseModel):
    """
    現在ユーザー情報レスポンス
    
    Attributes:
        email: ユーザーのメールアドレス
        display_name: 表示名（オプション）
        user_id: ユーザーID（オプション）
        role: ユーザーロール（オプション）
    """
    email: str = Field(..., description="ユーザーのメールアドレス")
    display_name: str | None = Field(None, description="ユーザーの表示名")
    user_id: str | None = Field(None, description="ユーザーID")
    role: str | None = Field(None, description="ユーザーロール")


@router.get(
    "/me",
    response_model=AuthMeResponse,
    summary="現在ユーザー情報取得",
    description="""
    現在ログインしているユーザーの情報を取得します。
    
    **認証方式は AUTH_MODE 環境変数で切り替え可能です：**
    
    - `AUTH_MODE=dummy`: 固定の開発用ユーザーを返す（DevAuthProvider）
      - 使用環境: local_dev, local_demo
      - 認証チェックなし、常に固定ユーザーを返す
    
    - `AUTH_MODE=vpn_dummy`: VPN経由の固定ユーザーを返す（VpnAuthProvider）
      - 使用環境: vm_stg（Tailscale/VPN経由）
      - VPN_USER_EMAIL, VPN_USER_NAME 環境変数で設定
    
    - `AUTH_MODE=iap`: Google Cloud IAP の JWT を検証（IapAuthProvider）
      - 使用環境: vm_prod（本番環境）
      - X-Goog-IAP-JWT-Assertion ヘッダーから JWT 署名を検証
      - IAP_AUDIENCE 環境変数に正しい audience 値の設定が必須
    
    **セキュリティ要件:**
    - 本番環境（STAGE=prod）では必ず AUTH_MODE=iap を設定してください
    - IAP_AUDIENCE が未設定の場合は起動時にエラーとなります
    """,
    responses={
        200: {
            "description": "ユーザー情報取得成功",
            "content": {
                "application/json": {
                    "examples": {
                        "dev_user": {
                            "summary": "開発環境（AUTH_MODE=dummy）",
                            "value": {
                                "email": "dev-user@honest-recycle.co.jp",
                                "display_name": "開発ユーザー",
                                "user_id": "dev_001",
                                "role": "admin"
                            }
                        },
                        "vpn_user": {
                            "summary": "ステージング環境（AUTH_MODE=vpn_dummy）",
                            "value": {
                                "email": "stg-admin@honest-recycle.co.jp",
                                "display_name": "STG Administrator",
                                "user_id": None,
                                "role": None
                            }
                        },
                        "iap_user": {
                            "summary": "本番環境（AUTH_MODE=iap）",
                            "value": {
                                "email": "user@honest-recycle.co.jp",
                                "display_name": "user",
                                "user_id": "iap_user",
                                "role": "user"
                            }
                        }
                    }
                }
            }
        },
        401: {
            "description": "認証失敗（IAP JWT ヘッダーなし、または署名検証失敗）",
        },
        403: {
            "description": "アクセス拒否（許可されていないドメイン等）",
        },
    }
)
async def get_me(
    request: Request,
    usecase: GetCurrentUserUseCase = Depends(get_get_current_user_usecase),
) -> AuthMeResponse:
    """
    現在ユーザー情報を取得
    
    Args:
        request: FastAPI Request オブジェクト
        usecase: GetCurrentUserUseCase（DI で注入）
    
    Returns:
        AuthMeResponse: ユーザーのメールアドレスと表示名
    """
    user = await usecase.execute(request)
    return AuthMeResponse(
        email=user.email,
        display_name=user.display_name,
        user_id=user.user_id,
        role=user.role,
    )
