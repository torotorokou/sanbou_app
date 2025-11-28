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
"""
from app.infra.db.db import get_db  # noqa: F401

__all__ = ["get_db"]
