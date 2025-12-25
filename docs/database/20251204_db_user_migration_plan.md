# DBユーザー分離・パスワード強化 移行計画

**作成日:** 2024-12-04  
**対象:** sanbou_app 全環境（dev / stg / prod）  
**目的:** セキュリティ強化と環境分離

---

## 📋 目次

1. [概要](#概要)
2. [前提条件](#前提条件)
3. [影響範囲](#影響範囲)
4. [移行手順](#移行手順)
5. [ロールバック手順](#ロールバック手順)
6. [トラブルシューティング](#トラブルシューティング)
7. [チェックリスト](#チェックリスト)

---

## 概要

### 現状の課題

- すべての環境で同一の DB ユーザー `myuser` を使用
- パスワードが弱い（`mypassword`）
- 環境間で権限が分離されていない

### 移行後の構成

| 環境         | ユーザー名        | 接続先DB      | 権限               |
| ------------ | ----------------- | ------------- | ------------------ |
| 開発         | `sanbou_app_dev`  | `sanbou_dev`  | CRUD + DDL         |
| ステージング | `sanbou_app_stg`  | `sanbou_stg`  | CRUD のみ          |
| 本番         | `sanbou_app_prod` | `sanbou_prod` | CRUD のみ          |
| 管理用       | `myuser`          | すべて        | マイグレーション用 |

### メリット

- ✅ **最小権限の原則**: 各環境に必要最小限の権限のみを付与
- ✅ **セキュリティ向上**: 環境間でクレデンシャルを分離
- ✅ **運用安全性**: 本番環境で DDL（テーブル削除等）を禁止

---

## 前提条件

### 必要なツール

```bash
# OpenSSL（パスワード生成用）
openssl version

# psql（PostgreSQL クライアント）
psql --version

# Docker Compose
docker compose version
```

### 事前確認事項

- [ ] 各環境のデータベースが正常に稼働している
- [ ] 現在のアプリケーションが正常に動作している
- [ ] データベースのバックアップが取得済み
- [ ] 作業時間帯の確保（本番環境: メンテナンス時間帯推奨）

---

## 影響範囲

### 変更対象ファイル

| カテゴリ         | ファイル                                               | 変更内容                                  | Git管理 |
| ---------------- | ------------------------------------------------------ | ----------------------------------------- | ------- |
| **環境変数**     | `env/.env.common`                                      | POSTGRES_USER/PASSWORD をプレースホルダ化 | ✅      |
| **環境変数**     | `env/.env.local_dev`                                   | コメント追加                              | ✅      |
| **環境変数**     | `env/.env.local_stg`                                   | コメント追加                              | ✅      |
| **環境変数**     | `env/.env.vm_stg`                                      | コメント追加                              | ✅      |
| **環境変数**     | `env/.env.vm_prod`                                     | コメント追加                              | ✅      |
| **シークレット** | `secrets/.env.local_dev.secrets`                       | 新ユーザー情報を追加                      | ❌      |
| **シークレット** | `secrets/.env.local_stg.secrets`                       | 新ユーザー情報を追加                      | ❌      |
| **シークレット** | `secrets/.env.vm_stg.secrets`                          | 新ユーザー情報を追加                      | ❌      |
| **シークレット** | `secrets/.env.vm_prod.secrets`                         | 新ユーザー情報を追加                      | ❌      |
| **SQL**          | `scripts/sql/20251204_alter_current_user_password.sql` | 新規作成                                  | ✅      |
| **SQL**          | `scripts/sql/20251204_create_app_db_users.sql`         | 新規作成                                  | ✅      |
| **ドキュメント** | `docs/db/20251204_db_user_design.md`                   | 新規作成                                  | ✅      |
| **ドキュメント** | `docs/db/20251204_db_user_migration_plan.md`           | 新規作成                                  | ✅      |

### サービス再起動が必要なコンポーネント

- `core_api`（DB 接続設定を読み込むため）
- `plan_worker`（同上）
- `ai_api`（同上）
- `ledger_api`（同上）
- `rag_api`（同上）

---

## 移行手順

### Phase 1: 準備（ダウンタイムなし）

#### ステップ 1-1: パスワード生成

各環境用の強力なパスワードを生成します。

```bash
# 開発環境用
echo "DEV:" $(openssl rand -base64 32)

# ステージング環境用
echo "STG:" $(openssl rand -base64 32)

# 本番環境用
echo "PROD:" $(openssl rand -base64 32)

# myuser 用（管理用）
echo "MYUSER:" $(openssl rand -base64 32)
```

**⚠️ 重要:** 生成したパスワードを安全な場所（1Password 等）に保存してください。

#### ステップ 1-2: 既存ユーザー（myuser）のパスワード強化

```bash
# 1. SQL テンプレートをコピー
cp scripts/sql/20251204_alter_current_user_password.sql /tmp/alter_user.sql

# 2. テキストエディタで開き、プレースホルダを置き換え
vim /tmp/alter_user.sql
# <NEW_STRONG_PASSWORD_FOR_MYUSER> → ステップ 1-1 で生成した MYUSER パスワード

# 3. 開発環境で実行（テスト）
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d postgres < /tmp/alter_user.sql

# 4. secrets ファイルも更新
vim secrets/.env.local_dev.secrets
# POSTGRES_PASSWORD を新しい myuser パスワードに変更

# 5. 他の環境でも同様に実行
# - ローカル STG: docker-compose.local_demo.yml
# - VM STG: VM にログインして実行
# - 本番: VM にログインして実行
```

#### ステップ 1-3: 環境別アプリユーザーの作成

```bash
# 1. SQL テンプレートをコピー
cp scripts/sql/20251204_create_app_db_users.sql /tmp/create_users.sql

# 2. テキストエディタで開き、プレースホルダを置き換え
vim /tmp/create_users.sql
# <DEV_DB_PASSWORD_PLACEHOLDER> → ステップ 1-1 で生成した DEV パスワード
# <STG_DB_PASSWORD_PLACEHOLDER> → ステップ 1-1 で生成した STG パスワード
# <PROD_DB_PASSWORD_PLACEHOLDER> → ステップ 1-1 で生成した PROD パスワード

# 3. 開発環境で実行
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev < /tmp/create_users.sql

# 4. ユーザーが作成されたことを確認
docker compose -f docker/docker-compose.dev.yml -p local_dev exec db \
  psql -U myuser -d sanbou_dev -c "\du"

# 5. 他の環境でも同様に実行
```

---

### Phase 2: アプリケーション設定変更（環境ごとに順次実施）

#### ステップ 2-1: 開発環境の切り替え

```bash
# 1. secrets ファイルを更新
vim secrets/.env.local_dev.secrets

# 以下の内容に変更:
# POSTGRES_USER=sanbou_app_dev
# POSTGRES_PASSWORD: ステップ1-1で生成したDEVパスワードを使用
# DATABASE_URL=postgresql://sanbou_app_dev:<DEVパスワード>@db:5432/sanbou_dev
# OPENAI_API_KEY=<既存の値>
# GEMINI_API_KEY=<既存の値>

# 2. アプリケーションを再起動
docker compose -f docker/docker-compose.dev.yml -p local_dev restart

# 3. 接続確認
docker compose -f docker/docker-compose.dev.yml -p local_dev logs core_api | grep -i "database"

# 4. 動作確認
# ブラウザで http://localhost:5173 にアクセスして正常に動作することを確認

# 5. 問題がなければ次の環境へ
```

**✅ 確認ポイント:**

- アプリケーションが正常に起動する
- データベース接続エラーが出ない
- 既存データが参照できる
- データの書き込みができる

#### ステップ 2-2: ローカル STG 環境の切り替え

開発環境と同様の手順で実施します。

```bash
# 1. secrets ファイルを更新
vim secrets/.env.local_stg.secrets

# POSTGRES_USER=sanbou_app_stg
# POSTGRES_PASSWORD: ステップ1-1で生成したSTGパスワードを使用
# DATABASE_URL=postgresql://sanbou_app_stg:<STGパスワード>@db:5432/sanbou_stg

# 2. 再起動・確認
docker compose -f docker/docker-compose.local_demo.yml restart
```

#### ステップ 2-3: VM STG 環境の切り替え

```bash
# VM にログイン
ssh user@stg-server

# 1. secrets ファイルを更新
vim /path/to/sanbou_app/secrets/.env.vm_stg.secrets

# POSTGRES_USER=sanbou_app_stg
# POSTGRES_PASSWORD: ステップ1-1で生成したSTGパスワードを使用
# DATABASE_URL=postgresql://sanbou_app_stg:<STGパスワード>@db:5432/sanbou_stg

# 2. コンテナ再起動
cd /path/to/sanbou_app
docker compose -f docker/docker-compose.stg.yml restart

# 3. ログ確認
docker compose -f docker/docker-compose.stg.yml logs -f core_api
```

#### ステップ 2-4: 本番環境の切り替え（慎重に実施）

**⚠️ 注意:**

- メンテナンス時間帯に実施
- ステークホルダーへの事前通知
- ロールバック手順の準備

```bash
# VM にログイン
ssh user@prod-server

# 1. データベースバックアップ
docker compose -f docker/docker-compose.prod.yml exec db \
  pg_dump -U myuser -d sanbou_prod -F c -f /tmp/backup_before_migration.dump

# 2. secrets ファイルを更新
vim /path/to/sanbou_app/secrets/.env.vm_prod.secrets

# POSTGRES_USER=sanbou_app_prod
# POSTGRES_PASSWORD: ステップ1-1で生成したPRODパスワードを設定
# DATABASE_URL=postgresql://sanbou_app_prod:<PRODパスワード>@db:5432/sanbou_prod

# 3. コンテナ再起動
cd /path/to/sanbou_app
docker compose -f docker/docker-compose.prod.yml restart

# 4. 動作確認
# - ヘルスチェック: curl https://sanbou-app.jp/health
# - 画面確認
# - ログ確認

# 5. 問題なければ完了
```

---

### Phase 3: 旧ユーザー（myuser）の権限縮小（オプション・2-4週間後）

**目的:** `myuser` を完全に廃止または管理専用に限定する

```sql
-- 1. SUPERUSER 権限を外す
ALTER USER myuser NOSUPERUSER;

-- 2. マイグレーション用の権限のみ付与
GRANT ALL PRIVILEGES ON DATABASE sanbou_dev TO myuser;
GRANT ALL PRIVILEGES ON DATABASE sanbou_stg TO myuser;
GRANT ALL PRIVILEGES ON DATABASE sanbou_prod TO myuser;

-- 3. 確認
\du myuser
```

---

## ロールバック手順

### 緊急時の復旧（Phase 2 で問題が発生した場合）

```bash
# 1. secrets ファイルを元に戻す
vim secrets/.env.<env>.secrets
# POSTGRES_USER=myuser
# POSTGRES_PASSWORD: 強化後のmyuserパスワードを設定
# DATABASE_URL=postgresql://myuser:<強化後のmyuserパスワード>@db:5432/sanbou_<env>

# 2. アプリケーション再起動
docker compose -f docker/docker-compose.<env>.yml restart

# 3. 正常性確認
```

**⚠️ 重要:** 新しいユーザー（`sanbou_app_*`）は削除せず、残しておいてください。次回の移行作業時に再利用できます。

---

## トラブルシューティング

### エラー 1: `FATAL: password authentication failed`

**原因:** パスワードが間違っている

**対処:**

```bash
# secrets ファイルのパスワードを確認
cat secrets/.env.<env>.secrets | grep POSTGRES_PASSWORD

# データベースに設定されているパスワードと一致するか確認
# 必要に応じて ALTER USER で再設定
```

### エラー 2: `permission denied for table`

**原因:** 新しいユーザーに権限が付与されていない

**対処:**

```bash
# 権限を再付与
docker compose exec db psql -U myuser -d sanbou_<env> \
  -c "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sanbou_app_<env>;"
```

### エラー 3: `relation does not exist`

**原因:** データベース名が間違っている

**対処:**

```bash
# DATABASE_URL のデータベース名を確認
cat secrets/.env.<env>.secrets | grep DATABASE_URL

# 正しいデータベース名に修正
```

### エラー 4: マイグレーションが失敗する

**原因:** `myuser` のパスワードが更新されていない、または Alembic が新しいユーザーで実行されている

**対処:**

```bash
# マイグレーションは myuser で実行する必要があります
docker compose exec \
  -e POSTGRES_USER=myuser \
  -e POSTGRES_PASSWORD_VAR=<myuserの新パスワード> \
  core_api alembic -c /backend/migrations/alembic.ini upgrade head
```

---

## チェックリスト

### 移行前

- [ ] すべての環境のデータベースバックアップを取得
- [ ] パスワードを生成し、1Password に保存
- [ ] ステークホルダーへの通知（本番環境の場合）
- [ ] ロールバック手順の確認

### 移行中

- [ ] `myuser` のパスワードを強化
- [ ] 環境別アプリユーザーを作成
- [ ] 開発環境で動作確認
- [ ] ローカル STG 環境で動作確認
- [ ] VM STG 環境で動作確認
- [ ] 本番環境で動作確認

### 移行後

- [ ] すべての環境で正常にアプリが起動することを確認
- [ ] データの読み書きが正常に動作することを確認
- [ ] マイグレーションが正常に実行できることを確認
- [ ] ログにエラーが出ていないことを確認
- [ ] `.env.common` に実パスワードが残っていないことを確認
- [ ] `secrets/` ディレクトリが Git 管理外になっていることを確認

### 長期運用（2-4週間後）

- [ ] `myuser` の SUPERUSER 権限を外す
- [ ] 運用上の問題がないことを確認

---

## 参考資料

- **DB ユーザー設計:** [docs/db/20251204_db_user_design.md](./20251204_db_user_design.md)
- **SQL スクリプト（パスワード変更）:** [scripts/sql/20251204_alter_current_user_password.sql](../../scripts/sql/20251204_alter_current_user_password.sql)
- **SQL スクリプト（ユーザー作成）:** [scripts/sql/20251204_create_app_db_users.sql](../../scripts/sql/20251204_create_app_db_users.sql)
- **環境変数サンプル:** [env/.env.example](../../env/.env.example)
- **シークレットテンプレート:** [secrets/.env.secrets.template](../../secrets/.env.secrets.template)

---

**作成者:** GitHub Copilot  
**最終更新:** 2024-12-04  
**バージョン:** 1.0
