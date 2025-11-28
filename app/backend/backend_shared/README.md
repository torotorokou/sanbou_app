
# backend-shared

共通ユーティリティ（Clean Architecture/SOLID原則準拠）、DB レイヤー（SQLAlchemy Async, トランザクション管理）、GCP ストレージ統合。

## アーキテクチャ

Clean Architecture / Hexagonal Architecture に基づいた層構造:

```
backend_shared/
├── core/                    # コア層（ビジネスロジック）
│   ├── domain/              # ドメインモデル（Entity, 値オブジェクト）
│   ├── ports/               # 抽象インターフェース（Repository, Gateway, FileStorage）
│   └── usecases/            # アプリケーションロジック（UseCase）
├── infra/                   # インフラストラクチャ層
│   ├── adapters/            # Ports の具体実装
│   │   ├── fastapi/         # FastAPI 統合
│   │   ├── middleware/      # ミドルウェア
│   │   └── presentation/    # プレゼンテーション層（Response モデル）
│   ├── storage/             # ファイルストレージ実装
│   │   ├── local_file_storage_repository.py   # ローカル実装
│   │   └── gcs_file_storage_repository.py     # GCS実装
│   ├── gcp/                 # GCP関連実装
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

## 新機能: GCP ストレージ統合 (2025-11-28)

backend_shared に GCP（主に GCS）のデータアクセスを集約しました。

### FileStoragePort

ローカルファイルシステムと GCS の両方に対応した抽象ポート:

```python
from backend_shared.core.ports.file_storage_port import FileStoragePort
from backend_shared.infra.storage.local_file_storage_repository import LocalFileStorageRepository
from backend_shared.infra.storage.gcs_file_storage_repository import GcsFileStorageRepository

# ローカル実装
storage = LocalFileStorageRepository(base_dir=Path("/data"))

# GCS実装
storage = GcsFileStorageRepository(
    bucket_name="my-bucket",
    base_prefix="my-app/data",
    credentials_path="/path/to/key.json"  # optional
)

# 統一インターフェース
data = storage.read_bytes("path/to/file.csv")
exists = storage.exists("path/to/file.csv")
files = storage.list_files("path/to/")
```

詳細は [GCP Storage Integration ドキュメント](../../docs/backend_shared/20251128_GCP_STORAGE_INTEGRATION.md) を参照してください。

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
