"""
FastAPI 依存性注入(DI)とユーティリティ - アプリケーション全体の共通依存関係

【概要】
FastAPIエンドポイントで使用する共通の依存関係（Dependencies）を一元管理します。
Dependency Injection パターンにより、テスタビリティと保守性を向上させます。

【主な機能】
1. get_db: データベースセッションの提供（トランザクション管理付き）
2. 将来的な拡張予定:
   - 認証・認可（get_current_user, require_admin等）
   - ログコンテキスト（request_id, user_context等）
   - リクエストスコープの設定
   - レート制限
   - キャッシュ管理

【設計方針】
- Centralized: すべてのFastAPI依存関係をこのモジュールで一元管理
- Testability: モックやスタブへの置き換えが容易
- Separation: ビジネスロジックからインフラストラクチャ層を分離
- Reusability: 複数のエンドポイントで再利用可能

【後方互換性】
app.infra.db.db から get_db を再エクスポートすることで、
既存コードの変更なしに段階的な移行が可能です。

【使用例】
```python
from app.deps import get_db
from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

router = APIRouter()

@router.get("/example")
def example_endpoint(db: Session = Depends(get_db)):
    '''
    データベースセッションを依存性注入で受け取る
    
    - セッションは自動的に生成・管理される
    - 正常終了時は自動コミット
    - 例外発生時は自動ロールバック
    - 終了時は必ずクローズ（コネクションプールに返却）
    '''
    result = db.query(MyModel).all()
    return result

# 複数の依存関係を組み合わせる例（将来）
@router.get("/secure")
def secure_endpoint(
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user),  # 認証（将来実装）
    # request_id: str = Depends(get_request_id),       # ログコンテキスト（将来実装）
):
    # 認証済みユーザーのデータを取得
    # user_data = db.query(UserData).filter_by(user_id=current_user.id).all()
    # return user_data
    pass
```

【将来の拡張例】
```python
# 認証・認可の依存関係（実装予定）
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    '''JWTトークンから現在のユーザーを取得'''
    # トークン検証とユーザー取得のロジック
    pass

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    '''管理者権限が必要なエンドポイント用'''
    if not current_user.is_admin:
        raise ForbiddenError(message="Admin access required")
    return current_user

# ログコンテキストの依存関係（実装予定）
def get_request_id(request: Request) -> str:
    '''リクエストIDを取得または生成'''
    return request.headers.get("X-Request-ID", str(uuid.uuid4()))
```
```
"""
import os
from fastapi import Request, Depends
from app.infra.db.db import get_db  # noqa: F401
from app.core.domain.auth.entities import AuthUser
from app.core.ports.auth.auth_provider import IAuthProvider
from app.infra.adapters.auth.dev_auth_provider import DevAuthProvider
from app.infra.adapters.auth.iap_auth_provider import IapAuthProvider

# ==========================================
# 認証プロバイダーのファクトリー（シングルトン）
# ==========================================

_auth_provider_instance: IAuthProvider | None = None

def get_auth_provider() -> IAuthProvider:
    """
    環境変数に基づいて適切な認証プロバイダーを返す（シングルトン）
    
    - IAP_ENABLED=true: IapAuthProvider（本番・ステージング）
    - IAP_ENABLED=false: DevAuthProvider（開発環境）
    
    プロバイダーは初回呼び出し時に一度だけ作成され、以降は同じインスタンスを再利用する。
    これにより、DevAuthProviderの初期化ログが大量に出力されることを防ぐ。
    
    Returns:
        IAuthProvider: 認証プロバイダーのインスタンス
    """
    global _auth_provider_instance
    
    if _auth_provider_instance is None:
        iap_enabled = os.getenv("IAP_ENABLED", "false").lower() == "true"
        
        if iap_enabled:
            _auth_provider_instance = IapAuthProvider()
        else:
            _auth_provider_instance = DevAuthProvider()
    
    return _auth_provider_instance


# ==========================================
# 認証依存関係
# ==========================================

async def get_current_user(
    request: Request,
    auth_provider: IAuthProvider = Depends(get_auth_provider)
) -> AuthUser:
    """
    現在のログインユーザーを取得
    
    全ての保護されたエンドポイントで使用する依存関係。
    IAP が有効な場合は JWT 検証を行い、開発環境では固定ユーザーを返す。
    
    Args:
        request: FastAPI Request オブジェクト
        auth_provider: 認証プロバイダー（自動注入）
    
    Returns:
        AuthUser: 認証済みユーザー情報
    
    Raises:
        HTTPException: 認証失敗時（401, 403）
    
    Usage:
        ```python
        @router.get("/protected")
        async def protected_endpoint(
            current_user: AuthUser = Depends(get_current_user)
        ):
            return {"email": current_user.email}
        ```
    """
    return await auth_provider.get_current_user(request)


async def get_optional_user(
    request: Request,
    auth_provider: IAuthProvider = Depends(get_auth_provider)
) -> AuthUser | None:
    """
    現在のユーザーを取得（オプショナル）
    
    認証は試みるが、失敗しても例外を投げない。
    公開エンドポイントで「ログイン済みなら追加情報を返す」ような用途に使用。
    
    Args:
        request: FastAPI Request オブジェクト
        auth_provider: 認証プロバイダー（自動注入）
    
    Returns:
        AuthUser | None: 認証済みユーザー情報、または None
    
    Usage:
        ```python
        @router.get("/public-but-personalized")
        async def public_endpoint(
            current_user: AuthUser | None = Depends(get_optional_user)
        ):
            if current_user:
                return {"message": f"Welcome back, {current_user.email}"}
            return {"message": "Welcome, guest"}
        ```
    """
    try:
        return await auth_provider.get_current_user(request)
    except Exception:
        return None


__all__ = ["get_db", "get_current_user", "get_optional_user", "get_auth_provider"]
