# DB接続失敗の包括的診断レポート

作成日: 2025-12-04  
対象環境: local_dev  
問題: PostgreSQLパスワード変更後に接続できなくなった

## 1. 問題の概要

ユーザーが `secrets/.env.local_dev.secrets` のパスワードを変更したことにより、以下のエラーが発生:

```
FATAL: password authentication failed for user "myuser"
```

## 2. 根本原因の特定

### 2.1 パスワード不整合の詳細

| 場所 | パスワード設定 | 状態 |
|------|--------------|------|
| **実際のDB (PostgreSQL)** | `mypassword` (例) | 変更されていない |
| **secrets/.env.local_dev.secrets** | `fOb1***[マスク済み]` (例) | 新しいパスワードに変更済み |
| **env/.env.local_dev (DATABASE_URL)** | `mypassword` (例) | **ハードコードされたまま** |
| **env/.env.common** | `__SET_IN_ENV_SPECIFIC_FILE__` | プレースホルダー |

### 2.2 問題の構造

```mermaid
graph TD
    A[Docker Compose起動] --> B[env_file読み込み順序]
    B --> C[1. env/.env.common]
    B --> D[2. env/.env.local_dev]
    B --> E[3. secrets/.env.local_dev.secrets]
    
    C --> F[POSTGRES_PASSWORD=__SET_IN_ENV_SPECIFIC_FILE__]
    D --> G[DATABASE_URL=postgresql://myuser:<OLD_PASSWORD>@db:5432/sanbou_dev]
    E --> H[POSTGRES_PASSWORD=<NEW_PASSWORD>]
    
    H --> I[DBコンテナ: 新パスワードで環境変数設定]
    I --> J{既存DBデータ存在?}
    J -->|Yes| K[既存のパスワード <OLD_PASSWORD> を使用]
    J -->|No| L[新パスワードで初期化]
    
    K --> M[実際のDBパスワード: <OLD_PASSWORD>]
    
    G --> N[アプリケーションコンテナ: DATABASE_URLを使用]
    N --> O[接続試行: mypassword]
    
    H --> P[アプリケーションコンテナ: POSTGRES_PASSWORDも設定]
    P --> Q[衝突: 2つの異なるパスワード設定]
    
    O --> R[成功するはずだが...]
    Q --> S[DATABASE_URLが優先される]
    S --> T[結果的に mypassword で接続成功]
    
    style K fill:#f96
    style H fill:#fc6
    style G fill:#f96
    style T fill:#6f6
```

## 3. 検証結果

### 3.1 ログ分析

```
db-1  | 2025-12-04 02:00:14.906 UTC [1] LOG:  database system is ready to accept connections
db-1  | 2025-12-04 02:00:31.123 UTC [41] FATAL:  password authentication failed for user "myuser"
```

**認証失敗が継続的に発生していたが、現在は接続できている理由:**

`env/.env.local_dev` の `DATABASE_URL=postgresql://myuser:<OLD_PASSWORD>@db:5432/sanbou_dev` (例) がそのまま残っているため、この接続文字列が優先されて接続に成功していた。

### 3.2 現在のコンテナ状態

```
local_dev-db-1            postgres:17-alpine      Up 4 minutes (healthy)
local_dev-core_api-1      local_dev-core_api      Up 4 minutes (healthy)
local_dev-ai_api-1        local_dev-ai_api        Up 4 minutes (healthy)
local_dev-ledger_api-1    local_dev-ledger_api    Up 4 minutes (healthy)
local_dev-rag_api-1       local_dev-rag_api       Up 4 minutes (healthy)
local_dev-plan_worker-1   local_dev-plan_worker   Up 4 minutes (unhealthy)
```

**重要な発見**: DB含めほぼ全てのサービスが正常に動作している。

### 3.3 実際のDB状態

```sql
\du
   Role name    |                         Attributes                         
----------------+------------------------------------------------------------
 app_readonly   | Cannot login
 myuser         | Superuser, Create role, Create DB, Replication, Bypass RLS
 sanbou_app_dev |
```

- `myuser`: スーパーユーザー、パスワードは `<OLD_PASSWORD>` (例) のまま
- `sanbou_app_dev`: 環境別ユーザーが既に作成されている(パスワード未設定の可能性)

## 4. なぜ現在は接続できているのか

### 4.1 環境変数の優先順位

Docker Composeの`env_file`は以下の順序で読み込まれますが、**後から読み込まれた値が前の値を上書き**します:

1. `../env/.env.common` - `POSTGRES_PASSWORD=__SET_IN_ENV_SPECIFIC_FILE__`
2. `../env/.env.local_dev` - `DATABASE_URL=postgresql://myuser:<OLD_PASSWORD>@db:5432/sanbou_dev` (例)
3. `../secrets/.env.local_dev.secrets` - `POSTGRES_PASSWORD=<NEW_PASSWORD>` (例、マスク済み)

### 4.2 実際の動作

1. **DBコンテナ**: PostgreSQLイメージは起動時に既存のDBデータディレクトリを検出
   - `PostgreSQL Database directory appears to contain a database; Skipping initialization`
   - **既存のパスワード (`<OLD_PASSWORD>` 例) をそのまま使用**
   - `POSTGRES_PASSWORD` 環境変数は既存DBには影響しない

2. **アプリケーションコンテナ**: 
   - `DATABASE_URL` 環境変数が明示的に接続文字列を指定
   - この中に `<OLD_PASSWORD>` (例) がハードコードされている
   - 個別の `POSTGRES_PASSWORD` 環境変数より `DATABASE_URL` が優先される
   - 結果: **古いパスワードで接続成功**

## 5. 設計上の問題点

### 5.1 DATABASE_URLのハードコード

```dotenv
# env/.env.local_dev (問題あり - 例)
DATABASE_URL=postgresql://myuser:<PASSWORD>@db:5432/sanbou_dev
```

**問題点:**
- パスワードが平文でGit管理ファイルに記載
- `POSTGRES_PASSWORD` 環境変数を使う設計なのに、DATABASE_URLで上書きされる
- 環境変数の分離設計が機能していない

### 5.2 Docker Composeのhealthcheck

```yaml
# docker/docker-compose.dev.yml (改善必要)
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U myuser -d sanbou_dev"]
```

**問題点:**
- ユーザー名 `myuser` がハードコード
- 環境変数を使用していない

### 5.3 PostgreSQLの初期化メカニズム

PostgreSQLコンテナは以下の動作をします:
- 初回起動時: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` で初期化
- 2回目以降: 既存データがあれば環境変数を無視して既存のパスワードを使用

**つまり、既存DBのパスワードを変更するには:**
1. SQLコマンドで直接変更する必要がある
2. または、データを削除して再初期化する

## 6. 推奨される修正方法

### オプション A: 正しい環境変数分離を実装（推奨）

#### Step 1: DATABASE_URLを環境変数から構築

`env/.env.local_dev`:
```dotenv
# ❌ 削除
# DATABASE_URL=postgresql://myuser:mypassword@db:5432/sanbou_dev

# ✅ 代わりに DATABASE_URL を構築しない（各サービスで組み立てる）
POSTGRES_DB=sanbou_dev
```

`secrets/.env.local_dev.secrets`:
```dotenv
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword  # 既存のパスワードに戻す
DATABASE_URL=postgresql://myuser:mypassword@db:5432/sanbou_dev
```

または、アプリケーションコード側で環境変数から動的に構築:
```python
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
```

#### Step 2: healthcheckを環境変数化

`docker/docker-compose.dev.yml`:
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
  interval: 10s
  timeout: 5s
  retries: 5
```

#### Step 3: 既存パスワードを使い続けるか、新パスワードへ移行

**Option A-1: 既存パスワードを使い続ける（最も安全）**
```bash
# secrets/.env.local_dev.secrets でパスワードを戻す (例)
POSTGRES_PASSWORD=<YOUR_CURRENT_PASSWORD>
```

**Option A-2: 新パスワードへ移行（データ保持）**
```bash
# 1. SQLでパスワード変更 (例: 実際のパスワードに置き換えてください)
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -c \
  "ALTER USER myuser WITH PASSWORD '<YOUR_NEW_PASSWORD>';"

# 2. secrets/.env.local_dev.secrets は変更済み
# 3. サービスを再起動
docker compose -f docker/docker-compose.dev.yml -p local_dev restart
```

**Option A-3: 新パスワードへ移行（データ削除）**
```bash
# 1. 全コンテナ停止・削除
docker compose -f docker/docker-compose.dev.yml -p local_dev down

# 2. PostgreSQLデータディレクトリを削除
rm -rf data/postgres_v17/*

# 3. 再起動（新パスワードで初期化）
docker compose -f docker/docker-compose.dev.yml -p local_dev up -d
```

### オプション B: 一時的な修正（推奨しない）

`secrets/.env.local_dev.secrets` を元のパスワードに戻す (例):
```dotenv
POSTGRES_PASSWORD=<YOUR_CURRENT_PASSWORD>
```

この方法は**根本的な設計問題を放置**するため推奨しません。

## 7. 将来の移行計画への影響

### 7.1 現在の移行計画の状況

以下の準備が完了:
- ✅ `docs/db/20251204_db_user_design.md` - 設計文書
- ✅ `docs/db/20251204_db_user_migration_plan.md` - 移行計画
- ✅ `scripts/sql/20251204_alter_current_user_password.sql` - パスワード変更SQL
- ✅ `scripts/sql/20251204_create_app_db_users.sql` - 新ユーザー作成SQL
- ⚠️ `sanbou_app_dev` ユーザーは既に作成されているが、パスワード未設定

### 7.2 推奨される次のステップ

1. **まず現在の問題を修正** (オプションA)
2. **sanbou_app_devユーザーのセットアップを完了**
   ```sql
   ALTER USER sanbou_app_dev WITH PASSWORD '<STRONG_PASSWORD>';
   GRANT ALL PRIVILEGES ON DATABASE sanbou_dev TO sanbou_app_dev;
   ```
3. **アプリケーションを sanbou_app_dev ユーザーに切り替え**
4. **myuser の使用を停止**（スーパーユーザーは緊急時のみ）

## 8. まとめ

### 8.1 即時の問題

- **現在は接続できている**: `env/.env.local_dev` の `DATABASE_URL` に古いパスワードがハードコードされているため
- **設計が機能していない**: 環境変数分離の意図が実装されていない

### 8.2 根本原因

1. `DATABASE_URL` が環境変数を使わずパスワードをハードコード
2. PostgreSQL初期化メカニズムの理解不足（既存DBは環境変数で変更不可）
3. healthcheckがユーザー名をハードコード

### 8.3 推奨アクション

**優先度1: DATABASE_URLの修正**
- `env/.env.local_dev` から `DATABASE_URL` を削除
- `secrets/.env.local_dev.secrets` に移動、または動的構築

**優先度2: パスワードの整合性**
- Option A-1: 既存パスワードを使い続ける（最も安全）
- Option A-2: SQLでDBパスワードを変更（データ保持）
- Option A-3: データ削除して再初期化（開発環境のみ）

**優先度3: 環境変数の完全分離**
- healthcheckの環境変数化
- 全ての接続設定をsecrets/に統一

## 9. 次のステップ

1. このレポートを確認
2. 修正方法を選択（Option A-1, A-2, A-3 のいずれか）
3. 選択した方法で修正を実装
4. 動作確認
5. 環境別ユーザー移行計画を続行
