# DBユーザー設計書

**作成日:** 2024-12-04  
**対象:** sanbou_app データベースセキュリティ強化  
**ステータス:** 設計

---

## 1. 概要

### 1.1 目的

現在、全環境で共有している単一のDBユーザー `myuser` を、環境別の専用ユーザーに分離することで、以下を実現します：

- **最小権限の原則**: 各環境のアプリケーションに必要最小限の権限のみを付与
- **セキュリティ向上**: 環境間でのクレデンシャル分離により、影響範囲を限定
- **運用安全性**: 本番環境では DDL（テーブル作成・削除）を禁止し、データ破壊リスクを低減

### 1.2 現状の課題

- すべての環境（dev / stg / prod）で同一ユーザー `myuser` を使用
- パスワードが弱い（`mypassword`）
- すべての環境で同じ権限を持つため、環境間の誤操作リスクが高い

---

## 2. 環境別DBユーザー設計

### 2.1 ユーザー一覧

| 環境             | ユーザー名        | 接続先DB      | 用途                 | 権限レベル                |
| ---------------- | ----------------- | ------------- | -------------------- | ------------------------- |
| **開発**         | `sanbou_app_dev`  | `sanbou_dev`  | アプリケーション接続 | CRUD + DDL（開発用）      |
| **ステージング** | `sanbou_app_stg`  | `sanbou_stg`  | アプリケーション接続 | CRUD のみ                 |
| **本番**         | `sanbou_app_prod` | `sanbou_prod` | アプリケーション接続 | CRUD のみ                 |
| **管理用**       | `myuser`          | すべて        | DBA作業・緊急対応    | SUPERUSER（段階的に縮小） |

---

## 3. 環境別権限ポリシー

### 3.1 開発環境（`sanbou_app_dev`）

**想定用途:**

- ローカル開発
- スキーマ変更のテスト
- マイグレーション実行

**付与権限:**

```sql
-- 基本権限
GRANT CONNECT ON DATABASE sanbou_dev TO sanbou_app_dev;
GRANT USAGE ON SCHEMA public TO sanbou_app_dev;

-- CRUD 権限
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sanbou_app_dev;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO sanbou_app_dev;

-- DDL 権限（開発環境のみ）
GRANT CREATE ON SCHEMA public TO sanbou_app_dev;

-- 今後追加されるテーブルにも自動付与
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sanbou_app_dev;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT USAGE, SELECT ON SEQUENCES TO sanbou_app_dev;
```

**理由:**

- 開発効率を優先し、テーブル作成などの DDL 操作を許可
- ただし SUPERUSER 権限は不要

---

### 3.2 ステージング環境（`sanbou_app_stg`）

**想定用途:**

- 本番デプロイ前の動作確認
- QA テスト
- マイグレーションは管理者が実行

**付与権限:**

```sql
-- 基本権限
GRANT CONNECT ON DATABASE sanbou_stg TO sanbou_app_stg;
GRANT USAGE ON SCHEMA public TO sanbou_app_stg;

-- CRUD 権限のみ
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sanbou_app_stg;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO sanbou_app_stg;

-- 今後追加されるテーブルにも自動付与
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sanbou_app_stg;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT USAGE, SELECT ON SEQUENCES TO sanbou_app_stg;
```

**制約:**

- DDL（CREATE TABLE / ALTER TABLE / DROP TABLE）は不可
- マイグレーションは管理者ユーザー（`myuser`）で実行

---

### 3.3 本番環境（`sanbou_app_prod`）

**想定用途:**

- 本番アプリケーション稼働
- エンドユーザーへのサービス提供

**付与権限:**

```sql
-- 基本権限
GRANT CONNECT ON DATABASE sanbou_prod TO sanbou_app_prod;
GRANT USAGE ON SCHEMA public TO sanbou_app_prod;

-- CRUD 権限のみ
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sanbou_app_prod;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO sanbou_app_prod;

-- 今後追加されるテーブルにも自動付与
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sanbou_app_prod;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT USAGE, SELECT ON SEQUENCES TO sanbou_app_prod;
```

**制約:**

- DDL は完全に禁止
- データ破壊リスクのある操作を制限
- マイグレーションは管理者ユーザー（`myuser`）で実行

---

### 3.4 管理用ユーザー（`myuser`）の今後の扱い

**現状:**

- SUPERUSER 権限を持つ全能ユーザー
- 開発・ステージング・本番すべてで使用

**移行後の用途:**

- マイグレーション実行（Alembic）
- スキーマ変更・インデックス作成
- DBA作業（バックアップ・リストア）
- 緊急時のデータ修正

**段階的な権限縮小計画:**

1. **Phase 1（移行直後）:**

   - アプリケーション接続を環境別ユーザーに切り替え
   - `myuser` のパスワードを強力なものに変更
   - アプリケーションは `myuser` を使用しない

2. **Phase 2（運用安定後、2-4週間後）:**

   - `myuser` の SUPERUSER 権限を外す
   - 必要な権限のみを明示的に付与（例：CREATE / ALTER / DROP）

   ```sql
   -- SUPERUSER を外す
   ALTER USER myuser NOSUPERUSER;

   -- マイグレーションに必要な権限を付与
   GRANT ALL PRIVILEGES ON DATABASE sanbou_dev TO myuser;
   GRANT ALL PRIVILEGES ON DATABASE sanbou_stg TO myuser;
   GRANT ALL PRIVILEGES ON DATABASE sanbou_prod TO myuser;
   ```

3. **Phase 3（長期運用後、必要に応じて）:**
   - `myuser` を廃止し、専用の管理者ユーザー（例：`sanbou_admin`）を新設
   - または `myuser` を管理専用として維持

---

## 4. スキーマ構造の考慮

### 4.1 現在のスキーマ構成

プロジェクトには `public` スキーマ以外にも以下のスキーマが存在する可能性があります：

- `raw`: 生データ
- `stg`: ステージングデータ
- `mart`: 分析用データマート

### 4.2 スキーマごとの権限設計

**開発環境（`sanbou_app_dev`）:**

```sql
-- すべてのスキーマへのアクセスを許可
GRANT USAGE ON SCHEMA raw, stg, mart TO sanbou_app_dev;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA raw TO sanbou_app_dev;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA stg TO sanbou_app_dev;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA mart TO sanbou_app_dev;
```

**ステージング・本番環境（`sanbou_app_stg` / `sanbou_app_prod`）:**

```sql
-- スキーマごとに最小権限
GRANT USAGE ON SCHEMA raw, stg, mart TO sanbou_app_stg;

-- raw: 書き込みのみ（分析データは参照しない想定）
GRANT INSERT ON ALL TABLES IN SCHEMA raw TO sanbou_app_stg;

-- stg: 読み書き
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA stg TO sanbou_app_stg;

-- mart: 読み取りのみ
GRANT SELECT ON ALL TABLES IN SCHEMA mart TO sanbou_app_stg;
```

**注意:**

- 実際のスキーマ構成を確認してから権限設定を調整してください
- 現時点で `raw` / `stg` / `mart` スキーマが存在しない場合は、`public` スキーマのみの権限設定で問題ありません

---

## 5. パスワード管理

### 5.1 パスワード生成

すべてのユーザーのパスワードは以下のコマンドで生成してください：

```bash
openssl rand -base64 32
```

**要件:**

- 32文字以上
- 英数字 + 記号を含む
- 環境ごとに異なるパスワードを使用

### 5.2 パスワード保管場所

| 環境                     | ファイル                         | Git管理 | 保管場所         |
| ------------------------ | -------------------------------- | ------- | ---------------- |
| 開発                     | `secrets/.env.local_dev.secrets` | ❌      | ローカルのみ     |
| ステージング（ローカル） | `secrets/.env.local_stg.secrets` | ❌      | ローカルのみ     |
| ステージング（VM）       | `secrets/.env.vm_stg.secrets`    | ❌      | VM上 + 1Password |
| 本番（VM）               | `secrets/.env.vm_prod.secrets`   | ❌      | VM上 + 1Password |

**重要:**

- `secrets/` ディレクトリ配下のファイルは `.gitignore` で除外されています
- 本番・ステージング環境のパスワードは必ず 1Password 等の安全な場所にバックアップしてください

---

## 6. 移行時の互換性維持

### 6.1 既存コードへの影響

環境変数 `DATABASE_URL` を環境別ユーザーを使うように変更するだけで、アプリケーションコードの変更は不要です：

**変更前（`.env.common` - 例）:**

```env
POSTGRES_USER=myuser  # 全環境で共通のスーパーユーザー（問題）
# POSTGRES_PASSWORD: 弱いパスワード（問題）
DATABASE_URL=postgresql://myuser:<WEAK_PASSWORD>@db:5432/sanbou_dev
```

**変更後（環境別ファイル + secrets）:**

```env
# env/.env.local_dev
POSTGRES_USER=sanbou_app_dev
POSTGRES_DB=sanbou_dev

# secrets/.env.local_dev.secrets
# POSTGRES_PASSWORD: secretsファイルに設定
DATABASE_URL=postgresql://sanbou_app_dev:<STRONG_PASSWORD>@db:5432/sanbou_dev
```

### 6.2 Alembic マイグレーション

マイグレーションは引き続き `myuser` で実行します：

```bash
# docker-compose で myuser を使ってマイグレーション実行
docker compose -f docker/docker-compose.dev.yml exec \
  -e POSTGRES_USER=myuser \
  -e POSTGRES_PASSWORD_MYUSER=<VALUE_FROM_SECRETS> \
  core_api alembic -c /backend/migrations/alembic.ini upgrade head
```

---

## 7. セキュリティチェックリスト

移行完了後、以下を確認してください：

- [ ] すべての環境で `myuser` の接続が不要になっている
- [ ] `.env.common` に実パスワードが残っていない
- [ ] `secrets/` ディレクトリのファイルが Git 管理外になっている
- [ ] 各環境のアプリケーションが正常に起動する
- [ ] マイグレーションが正常に実行できる
- [ ] 本番環境のパスワードが 1Password に保管されている
- [ ] 開発環境以外で DDL 権限がないことを確認

---

## 8. トラブルシューティング

### 8.1 接続エラーが発生する場合

```sql
-- ユーザーの存在確認
\du

-- ユーザーの権限確認
\du sanbou_app_dev

-- データベースへのアクセス権確認
\l
```

### 8.2 権限不足エラーが発生する場合

```sql
-- テーブルへのアクセス権確認
\dp

-- スキーマへのアクセス権確認
\dn+

-- 権限の再付与
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sanbou_app_dev;
```

---

## 9. 参考資料

- [PostgreSQL: ロールと権限](https://www.postgresql.org/docs/current/user-manag.html)
- [PostgreSQL: 権限管理のベストプラクティス](https://www.postgresql.org/docs/current/ddl-priv.html)
- [12 Factor App: 環境ごとの設定管理](https://12factor.net/ja/config)

---

**次のステップ:** [20251204_db_user_migration_plan.md](./20251204_db_user_migration_plan.md) を参照して、実際の移行作業を実施してください。
