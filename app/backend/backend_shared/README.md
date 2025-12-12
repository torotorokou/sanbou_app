
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

### データベースオブジェクト名定数

すべてのDBスキーマ・テーブル・ビュー・MVの名前は `backend_shared.db.names` で定数管理されています。

#### 基本的な使い方

```python
from backend_shared.db.names import (
    SCHEMA_MART,
    SCHEMA_STG,
    MV_RECEIVE_DAILY,
    T_SHOGUN_FINAL_RECEIVE,
    fq  # fully-qualified identifier 生成関数
)

# ✅ 推奨: 定数を使用
sql = f"SELECT * FROM {fq(SCHEMA_MART, MV_RECEIVE_DAILY)} WHERE ddate = :date"

# ❌ 非推奨: ハードコード（タイポのリスク）
sql = "SELECT * FROM mart.mv_receive_daily WHERE ddate = :date"
```

#### SQLファイルでの使用（テンプレートパターン）

**SQLファイル** (`app/infra/db/sql/example/query.sql`):
```sql
-- プレースホルダーを使用
SELECT *
FROM {mv_receive_daily}
WHERE ddate BETWEEN :start AND :end
```

**Pythonコード**:
```python
from backend_shared.db.names import SCHEMA_MART, MV_RECEIVE_DAILY, fq
from app.infra.db.sql_loader import load_sql
from sqlalchemy import text

class MyRepository:
    def __init__(self, db: Session):
        self.db = db
        # __init__ で SQL をロード・フォーマット・コンパイル（1回のみ）
        template = load_sql("example/query.sql")
        self._query_sql = text(
            template.format(
                mv_receive_daily=fq(SCHEMA_MART, MV_RECEIVE_DAILY)
            )
        )
    
    def fetch_data(self, start: date, end: date):
        # バインドパラメータでユーザー入力を安全に渡す
        result = self.db.execute(
            self._query_sql,
            {"start": start, "end": end}
        )
        return result.fetchall()
```

**重要**: 
- `.format()` は**定数のみ**に使用（スキーマ名、テーブル名）
- ユーザー入力は**必ずバインドパラメータ**（`:param_name`）で渡す
- これによりSQLインジェクションを防止

#### 利用可能な定数

**スキーマ** (6個):
- `SCHEMA_REF`, `SCHEMA_STG`, `SCHEMA_MART`, `SCHEMA_KPI`, `SCHEMA_RAW`, `SCHEMA_LOG`

**主要オブジェクト**:
- MV: `MV_RECEIVE_DAILY`, `MV_TARGET_CARD_PER_DAY` など
- テーブル: `T_SHOGUN_FINAL_RECEIVE`, `T_UPLOAD_FILE` など
- ビュー: `V_CALENDAR_CLASSIFIED`, `V_SALES_TREE_DETAIL_BASE` など

**コレクション**:
- `AUTO_REFRESH_MVS`: 自動更新対象のMV（2個）
- `SHOGUN_FINAL_TABLES`: 将軍確定データテーブル（3個）
- `SHOGUN_FLASH_TABLES`: 将軍速報データテーブル（3個）

完全なリストは `backend_shared/db/names.py` を参照してください。

---

### データベースURL構築

特殊文字を含むパスワードでも安全に接続できるよう、URLエンコードを自動で行います。

#### パターン1: 環境変数から自動構築（推奨）

```python
from backend_shared.infra.db import build_database_url_with_driver

# 環境変数 DATABASE_URL または POSTGRES_* から自動構築
DATABASE_URL = build_database_url_with_driver(driver="psycopg")
# => "postgresql+psycopg://user:encoded_password@host:5432/db"
```

#### パターン2: 明示的なパラメータ指定

```python
from backend_shared.infra.db import build_postgres_dsn

# パスワードに特殊文字（/, @, : など）が含まれても安全
DATABASE_URL = build_postgres_dsn(
    user="myuser",
    password="p@ss/w:rd",  # 自動的にURLエンコード
    host="localhost",
    port=5432,
    database="mydb",
    driver="psycopg"  # または "asyncpg", "psycopg2"
)
# => "postgresql+psycopg://myuser:p%40ss%2Fw%3Ard@localhost:5432/mydb"
```

**注意事項:**
- パスワードに `/`, `@`, `:` などが含まれる場合、自動的にURLエンコードされます
- 手動での文字列連結は避けてください（接続エラーの原因になります）

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
