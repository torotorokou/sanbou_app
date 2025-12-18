# Database Module

DB関連の全機能を提供するモジュールです。

## 📁 構造

```
backend_shared/db/
├── __init__.py           # 統合エクスポート
├── names.py              # DBオブジェクト名定数
├── url_builder.py        # DB接続URL構築
├── health.py             # ヘルスチェック
├── session.py            # セッション管理（新規）
└── shogun/               # 将軍データアクセス
    ├── dataset_keys.py
    ├── fetcher.py
    └── master_name_mapper.py
```

## 🔧 機能

### 1. DBオブジェクト名定数 (names.py)

テーブル名、ビュー名、スキーマ名などの定数を提供します。

```python
from backend_shared.db import SCHEMA_STG, fq

# スキーマ修飾名を取得
table_name = fq(SCHEMA_STG, "shogun_final_receive")
# => "stg.shogun_final_receive"
```

### 2. DB接続URL構築 (url_builder.py)

環境変数から安全にDB接続URLを構築します。

```python
from backend_shared.db import build_database_url_with_driver

# PostgreSQL接続URL構築
db_url = build_database_url_with_driver(driver="psycopg")
# => "postgresql+psycopg://user:pass@host:5432/dbname"
```

### 3. セッション管理 (session.py) ⭐ NEW

同期/非同期両対応のセッション管理を提供します。

#### 非同期セッション（FastAPI向け）

```python
from backend_shared.db import DatabaseSessionManager
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

# セッションマネージャー初期化
db_manager = DatabaseSessionManager(db_url)

# FastAPIエンドポイント
@app.get("/")
async def endpoint(session: AsyncSession = Depends(db_manager.get_session)):
    result = await session.execute(...)
    return result

# コンテキストマネージャー
async with db_manager.session_scope() as session:
    result = await session.execute(...)
    # 自動commit/rollback
```

#### 同期セッション（Worker/CLI向け）

```python
from backend_shared.db import SyncDatabaseSessionManager

# セッションマネージャー初期化
db_manager = SyncDatabaseSessionManager(db_url)

# コンテキストマネージャー
with db_manager.session_scope() as session:
    result = session.execute(...)
    # 自動commit/rollback

# 依存性注入
def my_function(session: Session = Depends(db_manager.get_session)):
    result = session.execute(...)
```

**設定オプション:**
```python
# 非同期
db_manager = DatabaseSessionManager(
    db_url,
    echo=True,              # SQLログ出力
    pool_pre_ping=True,     # 接続前のping確認
    pool_size=5,            # プールサイズ
    max_overflow=10,        # 追加接続数
)

# 同期
db_manager = SyncDatabaseSessionManager(
    db_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=0,         # Worker推奨: 0
    pool_recycle=3600,      # 接続リサイクル（秒）
)
```

### 4. ヘルスチェック (health.py)

DB接続状態を確認します。

```python
from backend_shared.db import ping_database

# DB接続確認
is_healthy = await ping_database(db_url)
```

### 5. 将軍データアクセス (shogun/)

将軍CSV（flash/final × receive/shipment/yard）のデータアクセスを提供します。

```python
from backend_shared.db import ShogunDatasetKey, ShogunDatasetFetcher

# データ取得
fetcher = ShogunDatasetFetcher(session)
data = fetcher.fetch(ShogunDatasetKey.SHOGUN_FINAL_RECEIVE)
```

詳細は [shogun/README.md](shogun/README.md) を参照してください。

## 📦 統合インポート

すべての機能は `backend_shared.db` から直接インポート可能です。

```python
from backend_shared.db import (
    # スキーマ
    SCHEMA_STG, SCHEMA_MART, SCHEMA_RAW,
    # ヘルパー関数
    fq, schema_qualified,
    # 接続ユーティリティ
    build_database_url_with_driver,
    ping_database,
    # セッション管理
    DatabaseSessionManager,
    SyncDatabaseSessionManager,
    # 将軍データアクセス
    ShogunDatasetKey,
    ShogunDatasetFetcher,
)
```

## 🔄 移行ガイド

### 旧: infra/frameworks/database.py

```python
# ❌ 非推奨
from backend_shared.infra.frameworks.database import DatabaseSessionManager
```

### 新: db/session.py

```python
# ✅ 推奨
from backend_shared.db import DatabaseSessionManager
```

### 旧: infra/db/

```python
# ❌ 非推奨
from backend_shared.infra.db import build_database_url
```

### 新: db/

```python
# ✅ 推奨
from backend_shared.db import build_database_url
```

## 🎯 設計方針

1. **Single Source of Truth**: DB関連の全機能を `backend_shared.db` に集約
2. **統一インターフェース**: 同期/非同期で一貫したAPI
3. **型安全性**: SQLAlchemy 2.x + 型ヒント
4. **後方互換性**: 既存コードは警告付きで動作

## 📚 関連ドキュメント

- [将軍データアクセス詳細](shogun/README.md)
- [リファクタリングレポート](../../docs/20251128_REFACTORING_REPORT.md)
