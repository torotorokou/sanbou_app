"""
Database Infrastructure - SQLAlchemy エンジンとセッション管理

【概要】
データベース接続とトランザクション管理を担当するインフラ層モジュール。
SQLAlchemy を使用した型安全かつ効率的なDB操作を提供します。

【主な機能】
1. コネクションプール管理
2. セッションライフサイクル管理
3. FastAPI 依存性注入対応
4. スキーマベースマルチテナンシー対応

【設計方針】
- シングルトンエンジン（@lru_cache により1インスタンスのみ）
- コネクションプール最適化（pool_size, max_overflow設定）
- 自動トランザクション管理（FastAPI Depends経由）
- スキーマベース権限分離（最小権限の原則）

【パフォーマンス最適化】
- pool_pre_ping: コネクション使用前の生存確認（stale connection対策）
- pool_recycle: 長時間未使用コネクションの自動再接続
- pool_size: 同時接続数の制御
- max_overflow: ピーク時の追加接続許可

【使用例】
```python
from app.deps import get_db
from fastapi import Depends
from sqlalchemy.orm import Session

@router.get("/example")
def example(db: Session = Depends(get_db)):
    # dbセッションは自動的にコミット/ロールバックされる
    result = db.query(Model).all()
    return result
```
"""

import os
from collections.abc import Generator
from functools import lru_cache

from backend_shared.infra.db.url_builder import build_database_url_with_driver
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# ========================================
# 環境変数の読み込み
# ========================================


DATABASE_URL = build_database_url_with_driver(driver="psycopg")
"""
データベース接続URL (SQLAlchemy 2.x + psycopg3 形式)
環境変数 DATABASE_URL から取得。未設定時は POSTGRES_* 環境変数から構築
"""

# ========================================
# SQLAlchemy 2.x + psycopg3 対応
# ========================================
# Note: build_database_url_with_driver() が既に postgresql+psycopg:// 形式で返すため
#       明示的な変換は不要


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """
    共有SQLAlchemyエンジンを取得または生成

    Returns:
        Engine: SQLAlchemyエンジンインスタンス（シングルトン）

    Description:
        @lru_cache により、アプリケーション全体で1つのエンジンのみを共有。
        コネクションプーリングによりパフォーマンスを最適化します。

    Pool設定:
        - pool_size: 維持する接続数（デフォルト: 8）
        - max_overflow: pool_size を超えて許可する追加接続数（デフォルト: 8）
        - pool_pre_ping: 接続使用前に生存確認（stale connection防止）
        - pool_recycle: 接続の自動リサイクル時間（30分、long-lived接続問題の回避）
        - echo: SQLログ出力（環境変数 SQL_ECHO=true で有効化）

    Notes:
        - Web APIサーバー: 現在の設定が推奨
        - 長時間実行ワーカー: NullPool 使用を検討（stale connection回避）

    Examples:
        >>> engine = get_engine()
        >>> with engine.connect() as conn:
        ...     result = conn.execute(text("SELECT 1"))
    """
    return create_engine(
        DATABASE_URL,
        pool_size=8,  # 同時接続数の上限
        max_overflow=8,  # ピーク時の追加接続許可数
        pool_pre_ping=True,  # 接続使用前の生存確認（重要）
        pool_recycle=1800,  # 30分でコネクションをリサイクル
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",  # SQLログ出力
        future=True,  # SQLAlchemy 2.x 互換モード
    )


# ========================================
# グローバルインスタンス
# ========================================

# Create engine with connection pooling
# For worker (long-running), consider NullPool to avoid stale connections
engine = get_engine()
"""
グローバルSQLAlchemyエンジン
アプリケーション起動時に1度だけ生成され、全体で共有されます
"""

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
"""
セッションファクトリー
新しいデータベースセッションを生成するためのファクトリー関数
- autocommit=False: 明示的なcommit()呼び出しが必要
- autoflush=False: 明示的なflush()呼び出しが必要（パフォーマンス向上）
"""

Base = declarative_base()
"""
ORMモデルの基底クラス
全てのORMモデルはこのクラスを継承します
"""


def get_db() -> Generator[Session, None, None]:
    """
    FastAPIエンドポイント用のデータベースセッション依存性

    Yields:
        Session: SQLAlchemy セッションインスタンス

    Description:
        FastAPI の Depends() で使用される依存性関数。
        セッションのライフサイクル（生成、コミット、ロールバック、クローズ）を自動管理します。

    トランザクション管理:
        - 成功時: 自動的に commit() を実行
        - 例外発生時: 自動的に rollback() を実行
        - 終了時: 必ず close() を実行（コネクションをプールに返却）

    使用例:
        ```python
        from app.deps import get_db
        from fastapi import Depends, APIRouter
        from sqlalchemy.orm import Session

        router = APIRouter()

        @router.get("/users")
        def get_users(db: Session = Depends(get_db)):
            users = db.query(User).all()
            return users
        ```

    Notes:
        - エンドポイント実行前にセッションが生成される
        - エンドポイント正常終了時、自動的にコミットされる
        - 例外発生時、自動的にロールバックされる
        - エンドポイント終了後、必ずクローズされる
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()  # 正常終了時は自動コミット
    except Exception:
        db.rollback()  # 例外発生時は自動ロールバック
        raise  # 例外を再送出
    finally:
        db.close()  # 必ずクローズ（コネクションをプールに返却）
