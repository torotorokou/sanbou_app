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
    
    認証方式（Dev / IAP / OAuth2）は環境変数 AUTH_MODE で切り替え可能です。
    - dev: 固定の開発用ユーザーを返す
    - iap: Google Cloud IAP のヘッダーからユーザー情報を抽出
    
    本番環境では必ず AUTH_MODE=iap を設定してください。
    """,
    responses={
        200: {
            "description": "ユーザー情報取得成功",
            "content": {
                "application/json": {
                    "example": {
                        "email": "user@honest-recycle.co.jp",
                        "display_name": "山田太郎"
                    }
                }
            }
        },
        401: {
            "description": "認証失敗（IAP ヘッダーなし等）",
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
