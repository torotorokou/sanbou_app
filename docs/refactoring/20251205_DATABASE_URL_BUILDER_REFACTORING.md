# Database URL Builder Refactoring - 2024年12月5日

## 概要

PostgreSQL接続URL（DSN）構築処理を`backend_shared`に集約し、パスワードに特殊文字（`/`, `@`, `:`など）が含まれても安全に接続できるように改善しました。

## 実施内容

### 1. 新規関数の追加

#### `build_postgres_dsn()` - 明示的パラメータ版

```python
from backend_shared.infra.db import build_postgres_dsn

dsn = build_postgres_dsn(
    user="myuser",
    password="p@ss/w:rd",  # 特殊文字を含むパスワード
    host="localhost",
    port=5432,
    database="mydb",
    driver="psycopg"
)
# => "postgresql+psycopg://myuser:p%40ss%2Fw%3Ard@localhost:5432/mydb"
```

**特徴:**

- パラメータを明示的に渡す形式
- user/passwordを自動的にURLエンコード
- `/`, `@`, `:` などの特殊文字を含むパスワードでも安全
- インフラ層（DB接続管理）専用

### 2. 既存関数の改善

#### `build_database_url()` - 環境変数版（内部リファクタリング）

内部実装を改善し、`build_postgres_dsn()`を利用するように変更しました。

```python
from backend_shared.infra.db import build_database_url

# 環境変数 DATABASE_URL または POSTGRES_* から自動構築
dsn = build_database_url(driver="psycopg")
```

**変更点:**

- 内部で`build_postgres_dsn()`を呼び出すように改善
- URLエンコードロジックの重複を排除
- 後方互換性を完全に維持

### 3. テストの追加

`tests/test_db_url_builder.py`に包括的なテストを追加しました。

**テスト項目:**

- 基本的なDSN構築
- パスワードに `/` を含む場合
- パスワードに `@` を含む場合
- パスワードに `:` を含む場合
- 複数の特殊文字を含む場合
- ユーザー名に特殊文字を含む場合
- 異なるドライバー（psycopg, asyncpg, psycopg2）
- ポート番号を文字列で指定
- DSN形式の妥当性
- 実際のVMで使われるような複雑なパスワード

**テスト結果:** 全10テスト合格 ✅

## 既存コードへの影響

### 影響なし - 既に適切に実装されていた箇所

以下のコンポーネントは既に`build_database_url()`または`build_database_url_with_driver()`を使用しており、変更不要：

1. **core_api** - `app/infra/db/db.py`

   ```python
   from backend_shared.infra.db.url_builder import build_database_url_with_driver
   DATABASE_URL = build_database_url_with_driver(driver="psycopg")
   ```

2. **plan_worker** - `app/config/settings.py`

   ```python
   from backend_shared.infra.db.url_builder import build_database_url_with_driver
   database_url: str = Field(default_factory=_build_database_url)
   ```

3. **plan_worker テスト** - `app/test/common.py`

   ```python
   from backend_shared.infra.db.url_builder import build_database_url
   return build_database_url(driver=None, raise_on_missing=True)
   ```

4. **rag_api, ai_api, ledger_api, manual_api**
   - これらのAPIはDB接続を使用していないため影響なし

### 内部リファクタリングのみ

`backend_shared.infra.db.url_builder.build_database_url()`の内部実装を改善しましたが、APIインターフェースは変更していません。

**Before:**

```python
# URLエンコードを直接実装
encoded_user = quote_plus(user)
encoded_password = quote_plus(password)
return f"{protocol}://{encoded_user}:{encoded_password}@{host}:{port}/{database}"
```

**After:**

```python
# 新しい build_postgres_dsn() を利用
return build_postgres_dsn(
    user=user,
    password=password,
    host=host,
    port=port,
    database=database,
    driver=driver,
)
```

## アーキテクチャ上の位置づけ

### レイヤー分離の遵守

```
┌─────────────────────────────────────────────┐
│ Domain Layer (core/domain)                  │
│ - ビジネスロジック                          │
│ - DB接続詳細を知らない ✅                   │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ Application Layer (usecases, config)        │
│ - ユースケース実装                          │
│ - 環境変数から設定を読む                    │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ Infrastructure Layer (infra/frameworks)     │ ← 今回の実装箇所
│ - DB接続管理                                │
│ - build_postgres_dsn() ✅                   │
│ - build_database_url() ✅                   │
│ - DatabaseSessionManager                    │
└─────────────────────────────────────────────┘
```

## 使用ガイドライン

### 新しいコードでの推奨パターン

#### パターン1: 環境変数から自動構築（推奨）

```python
from backend_shared.infra.db import build_database_url_with_driver

# 環境変数 DATABASE_URL または POSTGRES_* から自動構築
DATABASE_URL = build_database_url_with_driver(driver="psycopg")
```

#### パターン2: 明示的なパラメータ指定

```python
from backend_shared.infra.db import build_postgres_dsn

# パラメータを明示的に渡す
DATABASE_URL = build_postgres_dsn(
    user=settings.DB_USER,
    password=settings.DB_PASSWORD,
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    database=settings.DB_NAME,
    driver="psycopg"
)
```

### 避けるべきパターン ❌

```python
# ❌ 直接文字列連結（パスワードに特殊文字があると壊れる）
DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{db}"

# ❌ 手動でURLエンコード（エラーが起きやすい）
from urllib.parse import quote_plus
encoded_pass = quote_plus(password)
DATABASE_URL = f"postgresql://{user}:{encoded_pass}@{host}:{port}/{db}"
```

### 使うべきパターン ✅

```python
# ✅ backend_shared の共通関数を使う
from backend_shared.infra.db import build_postgres_dsn

DATABASE_URL = build_postgres_dsn(
    user=user,
    password=password,  # 特殊文字が含まれても安全
    host=host,
    port=port,
    database=database,
    driver="psycopg"
)
```

## セキュリティ上の改善

### 特殊文字を含むパスワードへの対応

**問題:**

```python
# パスワードが "p@ss/w:rd" の場合
dsn = f"postgresql://user:p@ss/w:rd@localhost:5432/db"
#                           ↑    ↑  ↑
#                           @ と / と : が URL の区切り文字として解釈される
# => 接続エラー
```

**解決:**

```python
# URLエンコードにより安全に
dsn = build_postgres_dsn(
    user="user",
    password="p@ss/w:rd",  # 自動的に p%40ss%2Fw%3Ard にエンコード
    host="localhost",
    port=5432,
    database="db",
    driver="psycopg"
)
# => "postgresql+psycopg://user:p%40ss%2Fw%3Ard@localhost:5432/db"
# => 接続成功 ✅
```

### エンコード表

| 文字 | エンコード | 用途                                           |
| ---- | ---------- | ---------------------------------------------- |
| `/`  | `%2F`      | パス区切り文字                                 |
| `@`  | `%40`      | ユーザー情報とホストの区切り                   |
| `:`  | `%3A`      | ユーザー名とパスワード、ホストとポートの区切り |
| `#`  | `%23`      | フラグメント識別子                             |
| `?`  | `%3F`      | クエリパラメータ開始                           |
| `&`  | `%26`      | クエリパラメータ区切り                         |

## 動作確認

### テスト実行結果

```bash
$ cd app/backend/backend_shared
$ python -m pytest tests/test_db_url_builder.py -v

tests/test_db_url_builder.py::TestBuildPostgresDsn::test_basic_dsn_construction PASSED [ 10%]
tests/test_db_url_builder.py::TestBuildPostgresDsn::test_password_with_slash PASSED [ 20%]
tests/test_db_url_builder.py::TestBuildPostgresDsn::test_password_with_at_sign PASSED [ 30%]
tests/test_db_url_builder.py::TestBuildPostgresDsn::test_password_with_colon PASSED [ 40%]
tests/test_db_url_builder.py::TestBuildPostgresDsn::test_password_with_multiple_special_chars PASSED [ 50%]
tests/test_db_url_builder.py::TestBuildPostgresDsn::test_username_with_special_chars PASSED [ 60%]
tests/test_db_url_builder.py::TestBuildPostgresDsn::test_different_drivers PASSED [ 70%]
tests/test_db_url_builder.py::TestBuildPostgresDsn::test_port_as_string PASSED [ 80%]
tests/test_db_url_builder.py::TestBuildPostgresDsn::test_dsn_format PASSED [ 90%]
tests/test_db_url_builder.py::TestUrlEncodingSafety::test_real_world_complex_password PASSED [100%]

10 passed in 0.11s ✅
```

### 既存テストへの影響

backend_sharedの既存テストで新規追加したコードに関連するエラーは発生していません。

一部のsmoke testが失敗していますが、これらは今回のリファクタリングとは無関係の既存の問題です。

## まとめ

### 達成したこと ✅

1. **共通関数の追加** - `build_postgres_dsn()` を実装
2. **既存関数の改善** - `build_database_url()` の内部リファクタリング
3. **包括的なテスト** - 特殊文字を含むパスワードでの動作を検証
4. **後方互換性の維持** - 既存コードは変更不要
5. **アーキテクチャの遵守** - Clean Architectureのレイヤー分離を維持

### 効果

- **セキュリティ向上**: パスワードに特殊文字が含まれても安全に接続可能
- **保守性向上**: DSN構築ロジックが一箇所に集約
- **テスト容易性**: 明示的なパラメータ渡しでテストが簡単
- **エラー削減**: 手動でのURLエンコード忘れを防止

### 今後の推奨事項

1. **新規コード**: `build_postgres_dsn()` または `build_database_url_with_driver()` を使用
2. **ドキュメント**: README に使用例を追加済み
3. **環境変数**: secrets ファイルでパスワードに特殊文字を使用可能

## 関連ファイル

- `app/backend/backend_shared/src/backend_shared/infra/db/url_builder.py` - 実装
- `app/backend/backend_shared/src/backend_shared/infra/db/__init__.py` - エクスポート
- `app/backend/backend_shared/tests/test_db_url_builder.py` - テスト
- `docs/refactoring/20251205_DATABASE_URL_BUILDER_REFACTORING.md` - このドキュメント

## 参考

- [SQLAlchemy Database URLs](https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls)
- [RFC 3986 - URI Generic Syntax](https://www.rfc-editor.org/rfc/rfc3986)
- [Python urllib.parse.quote_plus](https://docs.python.org/3/library/urllib.parse.html#urllib.parse.quote_plus)
