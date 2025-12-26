# DB User Migration: myuser → sanbou_app_dev

**日付**: 2025-12-24  
**優先度**: 🔴 HIGH（完了）  
**ステータス**: ✅ 修正完了

## 問題

`myuser`がスーパーユーザーとして作成され、多くのスキーマのオーナーになっていた。これにより：

- 環境変数で指定した`sanbou_app_dev`ユーザーとの不整合
- 権限エラーが発生する可能性
- セキュリティベストプラクティスに反する

## 実施した修正

### 1. スキーマオーナーの変更

```sql
-- myuserが所有していたスキーマをsanbou_app_devに移譲
ALTER SCHEMA app OWNER TO sanbou_app_dev;
ALTER SCHEMA app_auth OWNER TO sanbou_app_dev;
ALTER SCHEMA log OWNER TO sanbou_app_dev;
ALTER SCHEMA sandbox OWNER TO sanbou_app_dev;
ALTER SCHEMA ref OWNER TO sanbou_app_dev;
ALTER SCHEMA kpi OWNER TO sanbou_app_dev;
ALTER SCHEMA jobs OWNER TO sanbou_app_dev;
ALTER SCHEMA raw OWNER TO sanbou_app_dev;

-- appスキーマ内のテーブルオーナーも変更
ALTER TABLE IF EXISTS app.notification_outbox OWNER TO sanbou_app_dev;
ALTER TABLE IF EXISTS app.announcements OWNER TO sanbou_app_dev;
ALTER TABLE IF EXISTS app.announcement_user_states OWNER TO sanbou_app_dev;

-- 権限付与
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA app TO sanbou_app_dev;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA app TO sanbou_app_dev;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA app TO sanbou_app_dev;
```

### 2. 確認コマンド

```bash
# スキーマオーナー確認
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U sanbou_app_dev -d sanbou_dev -c "\dn+"

# ユーザー一覧確認
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U sanbou_app_dev -d sanbou_dev -c "\du"
```

## 結果

✅ 全スキーマのオーナーが`sanbou_app_dev`に変更済み（publicスキーマは除く）  
✅ `app.notification_outbox`テーブルが正常に作成・使用可能  
✅ DB-backed通知システムが正常動作

## 今後の対応

### 新規環境構築時の注意

新しい環境（vm_stg、vm_prod、local_demo）を構築する際：

1. **環境変数の確認**

   ```bash
   # 各環境の.envファイルでPOSTGRES_USERが正しく設定されていること
   cat env/.env.local_dev | grep POSTGRES_USER
   # POSTGRES_USER=sanbou_app_dev
   ```

2. **Baseline適用後の確認**

   ```bash
   make db-ensure-baseline-env ENV=<環境名>
   # schema_baseline.sqlは Owner: - を使用（環境変数のユーザーが自動的にオーナーになる）
   ```

3. **Roles Bootstrapの実行**

   ```bash
   make db-bootstrap-roles-env ENV=<環境名>
   # app_readonlyロールと権限を設定
   ```

4. **Alembic Migrationの実行**
   ```bash
   make al-up-env ENV=<環境名>
   # マイグレーションで作成されるテーブルは自動的にPOSTGRES_USERがオーナーになる
   ```

### Makefileのベストプラクティス

Makefileでは常に環境変数を使用：

```makefile
# ✅ Good: 環境変数を使用
$(DC_FULL) exec -T $(PG_SERVICE) sh -c '\
  psql -U "$$POSTGRES_USER" -d "$${POSTGRES_DB:-postgres}"'

# ❌ Bad: ハードコード
$(DC_FULL) exec -T db psql -U myuser -d sanbou_dev
```

### セキュリティ推奨事項

1. **スーパーユーザーの使用を最小限に**

   - アプリケーションユーザー（sanbou_app_dev）は通常ユーザー
   - スーパーユーザー操作が必要な場合のみ`myuser`を使用

2. **パスワード管理**

   - 全環境で`secrets/.env.*.secrets`にパスワードを保存
   - `POSTGRES_PASSWORD`は環境ごとに異なる強力なパスワードを使用

3. **権限の最小化**
   - 本番環境では読み取り専用ユーザー（app_readonly）の活用
   - スキーマごとに適切な権限設定

## 関連ファイル

- [env/.env.local_dev](../../../env/.env.local_dev#L33-L35) - POSTGRES_USER設定
- [makefile](../../../makefile#L302-L319) - 環境変数使用例（db-ensure-baseline-env）
- [scripts/db/bootstrap_roles.sql](../../../scripts/db/bootstrap_roles.sql) - ロール初期化
- [migrations_v2/sql/schema_baseline.sql](../../../app/backend/core_api/migrations_v2/sql/schema_baseline.sql) - ベースラインスキーマ

## 参考

- PostgreSQL: [Role Management](https://www.postgresql.org/docs/current/user-manag.html)
- Docker: [Environment Variables](https://docs.docker.com/compose/environment-variables/)
