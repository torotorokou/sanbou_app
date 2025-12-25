# データベースユーザー・ロール設計ガイド

## 概要

このドキュメントでは、sanbou_app におけるデータベースユーザーとロールの設計方針、推奨設定、および実装手順について説明します。

## 設計原則

### 1. 最小権限の原則 (Principle of Least Privilege)

各ユーザーは、その役割に必要な最小限の権限のみを持つべきです。

- **アプリケーション実行ユーザー**: SELECT, INSERT, UPDATE, DELETE のみ
- **マイグレーションユーザー**: DDL権限（CREATE, ALTER, DROP）
- **読み取り専用ユーザー**: SELECT のみ
- **DBA**: すべての権限（緊急時のみ使用）

### 2. 環境別のユーザー分離

各環境（dev / stg / prod）は専用のユーザーを持ち、パスワードも異なるべきです。

### 3. 接続情報の環境変数化

ハードコードを排除し、すべての接続情報を `.env` ファイルで管理します。

## 推奨ロール設計

### ロール一覧

| ロール名         | 用途                               | 権限レベル                           | 使用箇所                 |
| ---------------- | ---------------------------------- | ------------------------------------ | ------------------------ |
| `{env}_app_rw`   | アプリケーション実行用（読み書き） | DML (SELECT, INSERT, UPDATE, DELETE) | FastAPI実行時            |
| `{env}_app_ro`   | 読み取り専用（レポート等）         | SELECT のみ                          | 分析ツール、レポート生成 |
| `{env}_migrator` | マイグレーション実行用             | DDL (CREATE, ALTER, DROP) + DML      | Alembic実行時            |
| `{env}_dba`      | データベース管理者                 | SUPERUSER または広範な権限           | 緊急対応のみ             |

`{env}` は環境名（例: `dev`, `stg`, `prod`）を表します。

### 環境別ユーザー例

#### 開発環境 (local_dev)

```sql
-- アプリケーション実行用
CREATE USER sanbou_app_dev WITH PASSWORD '<STRONG_PASSWORD>';

-- マイグレーション用（開発環境では app と同じでも可）
-- 本番では分離を推奨
CREATE USER sanbou_migrator_dev WITH PASSWORD '<STRONG_PASSWORD>';

-- 読み取り専用（オプション）
CREATE USER sanbou_readonly_dev WITH PASSWORD '<STRONG_PASSWORD>';
```

#### ステージング環境 (vm_stg)

```sql
-- アプリケーション実行用
CREATE USER sanbou_app_stg WITH PASSWORD '<STRONG_PASSWORD>';

-- マイグレーション用
CREATE USER sanbou_migrator_stg WITH PASSWORD '<STRONG_PASSWORD>';

-- 読み取り専用（オプション）
CREATE USER sanbou_readonly_stg WITH PASSWORD '<STRONG_PASSWORD>';
```

#### 本番環境 (vm_prod)

```sql
-- アプリケーション実行用
CREATE USER sanbou_app_prod WITH PASSWORD '<STRONG_PASSWORD>';

-- マイグレーション用
CREATE USER sanbou_migrator_prod WITH PASSWORD '<STRONG_PASSWORD>';

-- 読み取り専用（オプション）
CREATE USER sanbou_readonly_prod WITH PASSWORD '<STRONG_PASSWORD>';

-- DBA用（緊急時のみ）
-- 注意: SUPERUSER は極力使用しない
CREATE USER sanbou_dba_prod WITH PASSWORD '<STRONG_PASSWORD>';
```

## 権限設定SQL雛形

### 1. アプリケーション実行用ユーザー (app_rw)

```sql
-- ユーザー作成
CREATE USER sanbou_app_dev WITH
    PASSWORD '<STRONG_PASSWORD>'
    NOCREATEDB
    NOCREATEROLE
    NOSUPERUSER;

-- データベースへの接続許可
GRANT CONNECT ON DATABASE sanbou_dev TO sanbou_app_dev;

-- スキーマ使用許可
GRANT USAGE ON SCHEMA public, raw, stg, mart, ref, app_schema TO sanbou_app_dev;

-- 既存テーブルへのDML権限
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sanbou_app_dev;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA raw TO sanbou_app_dev;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA stg TO sanbou_app_dev;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA mart TO sanbou_app_dev;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ref TO sanbou_app_dev;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA app_schema TO sanbou_app_dev;

-- シーケンスへの権限
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO sanbou_app_dev;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA raw TO sanbou_app_dev;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA stg TO sanbou_app_dev;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA mart TO sanbou_app_dev;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA ref TO sanbou_app_dev;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA app_schema TO sanbou_app_dev;

-- 将来作成されるテーブルへのデフォルト権限
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sanbou_app_dev;
ALTER DEFAULT PRIVILEGES IN SCHEMA raw GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sanbou_app_dev;
ALTER DEFAULT PRIVILEGES IN SCHEMA stg GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sanbou_app_dev;
ALTER DEFAULT PRIVILEGES IN SCHEMA mart GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sanbou_app_dev;
ALTER DEFAULT PRIVILEGES IN SCHEMA ref GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sanbou_app_dev;
ALTER DEFAULT PRIVILEGES IN SCHEMA app_schema GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sanbou_app_dev;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO sanbou_app_dev;
ALTER DEFAULT PRIVILEGES IN SCHEMA raw GRANT USAGE, SELECT ON SEQUENCES TO sanbou_app_dev;
ALTER DEFAULT PRIVILEGES IN SCHEMA stg GRANT USAGE, SELECT ON SEQUENCES TO sanbou_app_dev;
ALTER DEFAULT PRIVILEGES IN SCHEMA mart GRANT USAGE, SELECT ON SEQUENCES TO sanbou_app_dev;
ALTER DEFAULT PRIVILEGES IN SCHEMA ref GRANT USAGE, SELECT ON SEQUENCES TO sanbou_app_dev;
ALTER DEFAULT PRIVILEGES IN SCHEMA app_schema GRANT USAGE, SELECT ON SEQUENCES TO sanbou_app_dev;

-- Materialized View のリフレッシュ権限（必要に応じて）
-- GRANT SELECT, REFRESH ON ALL MATERIALIZED VIEWS IN SCHEMA mart TO sanbou_app_dev;
```

### 2. マイグレーション用ユーザー (migrator)

```sql
-- ユーザー作成
CREATE USER sanbou_migrator_dev WITH
    PASSWORD '<STRONG_PASSWORD>'
    CREATEDB           -- データベース作成権限（マイグレーションで必要な場合）
    NOCREATEROLE
    NOSUPERUSER;

-- データベースへの接続許可
GRANT CONNECT ON DATABASE sanbou_dev TO sanbou_migrator_dev;

-- スキーマ作成権限
GRANT CREATE ON DATABASE sanbou_dev TO sanbou_migrator_dev;

-- スキーマ使用許可
GRANT USAGE ON SCHEMA public, raw, stg, mart, ref, app_schema TO sanbou_migrator_dev;

-- DDL権限（CREATE, ALTER, DROP）
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sanbou_migrator_dev;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA raw TO sanbou_migrator_dev;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA stg TO sanbou_migrator_dev;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA mart TO sanbou_migrator_dev;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ref TO sanbou_migrator_dev;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA app_schema TO sanbou_migrator_dev;

-- シーケンスへの権限
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sanbou_migrator_dev;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA raw TO sanbou_migrator_dev;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA stg TO sanbou_migrator_dev;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA mart TO sanbou_migrator_dev;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ref TO sanbou_migrator_dev;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA app_schema TO sanbou_migrator_dev;

-- 将来作成されるオブジェクトへのデフォルト権限
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO sanbou_migrator_dev;
ALTER DEFAULT PRIVILEGES IN SCHEMA raw GRANT ALL PRIVILEGES ON TABLES TO sanbou_migrator_dev;
ALTER DEFAULT PRIVILEGES IN SCHEMA stg GRANT ALL PRIVILEGES ON TABLES TO sanbou_migrator_dev;
ALTER DEFAULT PRIVILEGES IN SCHEMA mart GRANT ALL PRIVILEGES ON TABLES TO sanbou_migrator_dev;
ALTER DEFAULT PRIVILEGES IN SCHEMA ref GRANT ALL PRIVILEGES ON TABLES TO sanbou_migrator_dev;
ALTER DEFAULT PRIVILEGES IN SCHEMA app_schema GRANT ALL PRIVILEGES ON TABLES TO sanbou_migrator_dev;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO sanbou_migrator_dev;
ALTER DEFAULT PRIVILEGES IN SCHEMA raw GRANT ALL PRIVILEGES ON SEQUENCES TO sanbou_migrator_dev;
ALTER DEFAULT PRIVILEGES IN SCHEMA stg GRANT ALL PRIVILEGES ON SEQUENCES TO sanbou_migrator_dev;
ALTER DEFAULT PRIVILEGES IN SCHEMA mart GRANT ALL PRIVILEGES ON SEQUENCES TO sanbou_migrator_dev;
ALTER DEFAULT PRIVILEGES IN SCHEMA ref GRANT ALL PRIVILEGES ON SEQUENCES TO sanbou_migrator_dev;
ALTER DEFAULT PRIVILEGES IN SCHEMA app_schema GRANT ALL PRIVILEGES ON SEQUENCES TO sanbou_migrator_dev;
```

### 3. 読み取り専用ユーザー (readonly)

```sql
-- ユーザー作成
CREATE USER sanbou_readonly_dev WITH
    PASSWORD '<STRONG_PASSWORD>'
    NOCREATEDB
    NOCREATEROLE
    NOSUPERUSER;

-- データベースへの接続許可
GRANT CONNECT ON DATABASE sanbou_dev TO sanbou_readonly_dev;

-- スキーマ使用許可
GRANT USAGE ON SCHEMA public, raw, stg, mart, ref, app_schema TO sanbou_readonly_dev;

-- SELECT権限のみ
GRANT SELECT ON ALL TABLES IN SCHEMA public TO sanbou_readonly_dev;
GRANT SELECT ON ALL TABLES IN SCHEMA raw TO sanbou_readonly_dev;
GRANT SELECT ON ALL TABLES IN SCHEMA stg TO sanbou_readonly_dev;
GRANT SELECT ON ALL TABLES IN SCHEMA mart TO sanbou_readonly_dev;
GRANT SELECT ON ALL TABLES IN SCHEMA ref TO sanbou_readonly_dev;
GRANT SELECT ON ALL TABLES IN SCHEMA app_schema TO sanbou_readonly_dev;

-- 将来作成されるテーブルへのデフォルト権限
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO sanbou_readonly_dev;
ALTER DEFAULT PRIVILEGES IN SCHEMA raw GRANT SELECT ON TABLES TO sanbou_readonly_dev;
ALTER DEFAULT PRIVILEGES IN SCHEMA stg GRANT SELECT ON TABLES TO sanbou_readonly_dev;
ALTER DEFAULT PRIVILEGES IN SCHEMA mart GRANT SELECT ON TABLES TO sanbou_readonly_dev;
ALTER DEFAULT PRIVILEGES IN SCHEMA ref GRANT SELECT ON TABLES TO sanbou_readonly_dev;
ALTER DEFAULT PRIVILEGES IN SCHEMA app_schema GRANT SELECT ON TABLES TO sanbou_readonly_dev;
```

## 環境変数設定例

### アプリケーション用 (.env ファイル)

```env
# env/.env.local_dev
DB_USER=sanbou_app_dev
DB_PASSWORD=<SET_IN_SECRETS_FILE>
DB_NAME=sanbou_dev
DB_HOST=db
DB_PORT=5432

# マイグレーション用（オプション）
# 未設定の場合は DB_USER にフォールバック
# DB_MIGRATOR_USER=sanbou_migrator_dev
# DB_MIGRATOR_PASSWORD=<SET_IN_SECRETS_FILE>
```

### シークレット管理 (secrets/.env.{env}.secrets)

```env
# secrets/.env.local_dev.secrets
DB_PASSWORD=<STRONG_PASSWORD_HERE>
DB_MIGRATOR_PASSWORD=<STRONG_PASSWORD_HERE>
```

## 運用ルール

### 1. パスワード管理

- **強力なパスワードを使用**: 最低32文字、ランダム生成推奨
  ```bash
  openssl rand -base64 32
  ```
- **環境ごとに異なるパスワードを設定**
- **secrets/ ディレクトリは .gitignore に追加**（既に対応済み）
- **パスワードローテーション**: 最低年1回、セキュリティインシデント時は即座に

### 2. ユーザー使用ガイドライン

#### アプリケーション実行時

- **使用ユーザー**: `{env}_app_rw`
- **接続方法**: DB_USER / DB_PASSWORD 環境変数
- **用途**: FastAPI、ワーカー等の通常実行

#### マイグレーション実行時

- **使用ユーザー**: `{env}_migrator`（未設定時は app にフォールバック）
- **接続方法**: DB_MIGRATOR_USER / DB_MIGRATOR_PASSWORD 環境変数
- **用途**: Alembic マイグレーション、スキーマ変更

#### データベース管理作業

- **使用ユーザー**: `{env}_dba` または postgres ユーザー
- **接続方法**: 手動接続（psql等）
- **用途**: 緊急対応、大規模メンテナンス

### 3. 禁止事項

- ❌ **myuser等のハードコード**: すべて環境変数から取得
- ❌ **SUPERUSER の常用**: 緊急時以外は使用禁止
- ❌ **本番環境でのアドホックDDL**: 必ずマイグレーション経由
- ❌ **パスワードの平文保存**: secrets/ 以外には記載しない

## マイグレーション手順

### 既存環境へのユーザー追加（段階的移行）

#### Phase 1: ユーザー作成（既存システムに影響なし）

```sql
-- 1. パスワード生成
-- ローカルPC上で実行:
echo "APP_USER:" $(openssl rand -base64 32)
echo "MIGRATOR:" $(openssl rand -base64 32)
echo "READONLY:" $(openssl rand -base64 32)

-- 2. ユーザー作成
-- DB上で実行:
\i /path/to/create_users_dev.sql
```

#### Phase 2: 権限付与

```sql
-- DB上で実行:
\i /path/to/grant_permissions_dev.sql
```

#### Phase 3: アプリケーション設定変更

```bash
# 1. .env ファイル更新
vim env/.env.local_dev
# DB_USER=sanbou_app_dev を追加

# 2. secrets ファイル更新
vim secrets/.env.local_dev.secrets
# DB_PASSWORD=<生成したパスワード> を追加

# 3. アプリケーション再起動
make down ENV=local_dev
make up ENV=local_dev

# 4. 動作確認
curl http://localhost:8002/health
```

#### Phase 4: 旧ユーザー削除（オプション、安全確認後）

```sql
-- 注意: 十分なテスト期間（2-4週間）後に実施
-- DROP USER myuser;
```

## 検証方法

### ユーザー一覧確認

```sql
-- PostgreSQL上で実行
\du

-- または
SELECT usename, usecreatedb, usesuper FROM pg_user ORDER BY usename;
```

### 権限確認

```sql
-- 特定スキーマのテーブル権限確認
\dp raw.*

-- または
SELECT
    schemaname,
    tablename,
    tableowner,
    has_table_privilege('sanbou_app_dev', schemaname||'.'||tablename, 'SELECT') as can_select,
    has_table_privilege('sanbou_app_dev', schemaname||'.'||tablename, 'INSERT') as can_insert
FROM pg_tables
WHERE schemaname IN ('public', 'raw', 'stg', 'mart', 'ref', 'app_schema')
ORDER BY schemaname, tablename;
```

### 接続テスト

```bash
# app ユーザーで接続テスト
psql "postgresql://sanbou_app_dev:<PASSWORD>@localhost:5432/sanbou_dev" -c "SELECT 1;"

# migrator ユーザーで接続テスト
psql "postgresql://sanbou_migrator_dev:<PASSWORD>@localhost:5432/sanbou_dev" -c "SELECT 1;"
```

## トラブルシューティング

### Q1: "password authentication failed" エラー

**原因**: パスワードが間違っているか、ユーザーが存在しない

**解決策**:

1. ユーザーが作成されているか確認: `\du` (psql上)
2. secrets ファイルのパスワードを確認
3. 環境変数が正しく読み込まれているか確認: `env | grep DB_`

### Q2: "permission denied for table" エラー

**原因**: テーブルへのアクセス権限がない

**解決策**:

1. 権限確認: `\dp <schema>.<table>`
2. GRANT文を再実行
3. ALTER DEFAULT PRIVILEGES が設定されているか確認

### Q3: マイグレーション実行時のエラー

**原因**: migrator ユーザーに DDL権限がない

**解決策**:

1. DB_MIGRATOR_USER が設定されているか確認
2. migrator ユーザーの権限を確認
3. 必要に応じて ALL PRIVILEGES を付与

## 関連ドキュメント

- [DATABASE_URL_BUILDER_REFACTORING.md](../refactoring/20251205_DATABASE_URL_BUILDER_REFACTORING.md): URL構築ロジックの詳細
- [db_user_design.md](./20251204_db_user_design.md): ユーザー設計の背景
- [db_user_migration_plan.md](./20251204_db_user_migration_plan.md): 移行計画

## 更新履歴

- 2025-12-24: 初版作成（myuser廃止、env統一、権限分離の仕込み）
