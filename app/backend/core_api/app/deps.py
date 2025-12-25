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
from typing import Generator

from app.core.domain.auth.entities import AuthUser
from app.core.ports.auth.auth_provider import IAuthProvider
from app.infra.adapters.auth.dev_auth_provider import DevAuthProvider
from app.infra.adapters.auth.iap_auth_provider import IapAuthProvider
from app.infra.adapters.auth.vpn_auth_provider import VpnAuthProvider
from app.infra.db.db import get_db  # noqa: F401
from app.infra.db.db import get_engine
from fastapi import Depends, Request
from sqlalchemy.orm import Session

# ==========================================
# データベースセッション（将来のマイグレーション用接続分離対応）
# ==========================================


def get_db_session_app() -> Generator[Session, None, None]:
    """
    アプリケーション実行用のDBセッションを提供

    通常のアプリケーション実行時に使用。
    将来的には DB_USER / DB_PASSWORD で接続する専用ユーザーに変更予定。

    現在は get_db() と同等（後方互換性）。

    Yields:
        Session: SQLAlchemyセッション

    Example:
        ```python
        @router.get("/users")
        def get_users(db: Session = Depends(get_db_session_app)):
            return db.query(User).all()
        ```
    """
    # 現在は通常の get_db と同じ
    # 将来: DB_USER / DB_PASSWORD による専用接続
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


def get_db_session_migrator() -> Generator[Session, None, None]:
    """
    マイグレーション用のDBセッションを提供（DDL操作用）

    Alembic等のマイグレーションツールから使用。
    将来的には DB_MIGRATOR_USER / DB_MIGRATOR_PASSWORD で接続する
    DDL権限を持つ専用ユーザーに変更予定。

    現在は get_db() と同等だが、将来の分離に備えたインターフェース。
    DB_MIGRATOR_USER が未設定の場合は app と同じユーザーを使用（フォールバック）。

    Yields:
        Session: SQLAlchemyセッション

    Example:
        ```python
        # Alembic env.py での使用例
        from app.deps import get_db_session_migrator

        def run_migrations():
            db = next(get_db_session_migrator())
            try:
                # migration operations
                pass
            finally:
                db.close()
        ```

    Notes:
        - 通常のアプリケーションコードからは使用しない
        - マイグレーションツール専用
        - CREATE / ALTER / DROP 等のDDL権限が必要
    """
    # 現在は通常の get_db と同じ（フォールバック）
    # 将来: DB_MIGRATOR_USER / DB_MIGRATOR_PASSWORD による専用接続
    #       未設定時は app ユーザーにフォールバック
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


# ==========================================
# 認証プロバイダーのファクトリー（シングルトン）
# ==========================================

_auth_provider_instance: IAuthProvider | None = None


def get_auth_provider() -> IAuthProvider:
    """
    環境変数 AUTH_MODE に基づいて適切な認証プロバイダーを返す（シングルトン）

    AUTH_MODE の値:
    - "dummy": DevAuthProvider（ローカル開発環境、認証なし）
    - "vpn_dummy": VpnAuthProvider（VPN/Tailscale 経由、固定ユーザー）
    - "iap": IapAuthProvider（本番環境、IAP ヘッダ検証）

    プロバイダーは初回呼び出し時に一度だけ作成され、以降は同じインスタンスを再利用する。
    これにより、初期化ログが大量に出力されることを防ぐ。

    環境別推奨設定:
    - local_dev: AUTH_MODE=dummy
    - vm_stg: AUTH_MODE=vpn_dummy (VPN_USER_EMAIL, VPN_USER_NAME 設定推奨)
    - vm_prod: AUTH_MODE=iap (IAP_AUDIENCE, IAP_PUBLIC_KEY_URL 必須)

    Returns:
        IAuthProvider: 認証プロバイダーのインスタンス

    Raises:
        ValueError: AUTH_MODE が不正な値、または本番環境で安全性チェック失敗の場合
    """
    global _auth_provider_instance

    if _auth_provider_instance is None:
        auth_mode = os.getenv("AUTH_MODE", "dummy").lower()
        stage = os.getenv("STAGE", "dev")

        # 本番環境での安全性チェック
        if stage == "prod":
            if auth_mode != "iap":
                raise ValueError(
                    f"🔴 SECURITY ERROR: Production must use AUTH_MODE=iap, got '{auth_mode}'. "
                    f"Set AUTH_MODE=iap in env/.env.vm_prod"
                )
            iap_audience = os.getenv("IAP_AUDIENCE", "")
            if not iap_audience:
                raise ValueError(
                    "🔴 SECURITY ERROR: IAP_AUDIENCE must be set in production! "
                    "Get the audience value from GCP Console:\n"
                    "  1. Go to: Security > Identity-Aware Proxy\n"
                    "  2. Find your backend service\n"
                    "  3. Copy the audience value (format: /projects/PROJECT_NUMBER/global/backendServices/SERVICE_ID)\n"
                    "  4. Set IAP_AUDIENCE in secrets/.env.vm_prod.secrets"
                )

        if auth_mode == "dummy":
            _auth_provider_instance = DevAuthProvider()
        elif auth_mode == "vpn_dummy":
            _auth_provider_instance = VpnAuthProvider()
        elif auth_mode == "iap":
            _auth_provider_instance = IapAuthProvider()
        else:
            raise ValueError(
                f"Invalid AUTH_MODE: {auth_mode}. "
                f"Supported values: dummy, vpn_dummy, iap"
            )

    return _auth_provider_instance


# ==========================================
# 認証依存関係
# ==========================================


async def get_current_user(
    request: Request, auth_provider: IAuthProvider = Depends(get_auth_provider)
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
    request: Request, auth_provider: IAuthProvider = Depends(get_auth_provider)
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
