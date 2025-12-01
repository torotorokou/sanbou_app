
# backend-shared

共通ユーティリティ（Clean Architecture/SOLID原則準拠）と DB レイヤー（SQLAlchemy Async, トランザクション管理）。

## アーキテクチャ

Clean Architecture / Hexagonal Architecture に基づいた層構造:

```
backend_shared/
├── core/                    # コア層（ビジネスロジック）
│   ├── domain/              # ドメインモデル（Entity, 値オブジェクト）
│   ├── ports/               # 抽象インターフェース（Repository, Gateway）
│   └── usecases/            # アプリケーションロジック（UseCase）
├── infra/                   # インフラストラクチャ層
│   ├── adapters/            # Ports の具体実装
│   │   ├── fastapi/         # FastAPI 統合
│   │   ├── middleware/      # ミドルウェア
│   │   └── presentation/    # プレゼンテーション層（Response モデル）
│   └── frameworks/          # フレームワーク固有処理
│       ├── database.py      # DB 接続・Session 管理
│       └── logging_utils/   # ログ設定
├── config/                  # 設定管理・DI
│   ├── config_loader.py     # 設定ファイル読み込み
│   ├── paths.py             # パス管理
│   └── di_providers.py      # 依存関係の組み立て
└── utils/                   # 共通ユーティリティ
```

### 依存関係のルール

- **core** は他のどの層にも依存しない（純粋なビジネスロジック）
- **infra** は core に依存する（依存関係逆転の原則）
- **config** で依存関係を組み立てる（DI コンテナ）

## 使い方（各サービス側）

### DB セッション管理

```python
# deps.py（例：core_api）
from backend_shared.config.di_providers import provide_database_session_manager

DB_URL = "postgresql+asyncpg://user:pass@db:5432/app"
db_manager = provide_database_session_manager(DB_URL)

async def get_session():
    async with db_manager.session_scope() as session:
        yield session

# ルーター例
@router.put("/users/{user_id}")
async def update_user(user_id: int, body: UserUpdate, session: AsyncSession = Depends(get_session)):
    user = await session.get(User, user_id)
    user.name = body.name
    # commit は session_scope が実施
    return {"ok": True}
```

### CSV フォーマッター

```python
from backend_shared.config.di_providers import provide_csv_formatter

# DI コンテナから CSV フォーマッターを取得
formatter = provide_csv_formatter(csv_type="shipment")

# DataFrame を整形（raw_df は pandas の DataFrame で CSV 読込済みのもの）
clean_df = formatter.format(raw_df)
```

### 手動での組み立て（詳細制御が必要な場合）

```python
from backend_shared.config.config_loader import ShogunCsvConfigLoader
from backend_shared.core.usecases.csv_formatter.formatter_config import build_formatter_config
from backend_shared.core.usecases.csv_formatter.formatter_factory import CSVFormatterFactory

# 1. 設定ファイル（YAML）からローダーを作成
loader = ShogunCsvConfigLoader()

# 2. build_formatter_config で FormatterConfig を作成（例: "shipment" = 出荷一覧）
config = build_formatter_config(loader, "shipment")

# 3. Factory から Formatter を取得
formatter = CSVFormatterFactory.create(config)

# 4. DataFrame を整形
clean_df = formatter.format(raw_df)
```
