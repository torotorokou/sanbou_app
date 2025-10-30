
# backend-shared

共通ユーティリティ（Clean Architecture/SOLID原則準拠）と DB レイヤー（SQLAlchemy Async, トランザクション管理）。

## 使い方（各サービス側）

### DB セッション管理

```python
# deps.py（例：core_api）
from backend_shared.db.database import DatabaseSessionManager

DB_URL = "postgresql+asyncpg://user:pass@db:5432/app"
db = DatabaseSessionManager(DB_URL)

async def get_session():
    async with db.session_scope() as session:
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
from backend_shared.config.config_loader import SyogunCsvConfigLoader
from backend_shared.formatter.formatter_config import build_formatter_config, FormatterConfig
from backend_shared.formatter.formatter import CSVFormatter

# 1. 設定ファイル（YAML）からローダーを作成
loader = SyogunCsvConfigLoader()

# 2. build_formatter_configでFormatterConfigを作成（例: "shipment" = 出荷一覧）
config = build_formatter_config(loader, "shipment")

# 3. FormatterにConfigを渡して初期化
formatter = CSVFormatter(config)

# 4. DataFrameを整形（raw_dfはpandasのDataFrameでCSV読込済みのもの）
clean_df = formatter.format(raw_df)
```
