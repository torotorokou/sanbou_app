"""
FastAPI 依存性注入(DI)とユーティリティ

このモジュールはFastAPIエンドポイントで使用する共通の依存関係を提供します。

主な機能:
  - get_db: データベースセッションの提供(トランザクション管理付き)
  - 将来的な拡張: 認証、ログコンテキスト、リクエストスコープの設定など

後方互換性のため、app.infra.db.db から get_db を再エクスポートしています。
すべてのFastAPI依存関係を一元管理する場所として機能します。

使用例:
    from app.deps import get_db
    from fastapi import Depends
    
    @router.get("/example")
    def example(db: Session = Depends(get_db)):
        # dbセッションを使用した処理
        ...
"""
from app.infra.db.db import get_db  # noqa: F401

__all__ = ["get_db"]
