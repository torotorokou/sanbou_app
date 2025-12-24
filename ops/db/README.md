# DB権限・ロール・所有者 統合管理

**作成日**: 2025-12-24  
**目的**: PostgreSQL の権限エラーを根絶し、安全で保守可能なロール設計を実現する

---

## 📋 概要

### なぜ owner を分けるか

- **セキュリティ**: アプリ接続ユーザーに不要な権限を与えない（最小権限の原則）
- **保守性**: 所有者を統一することで、権限管理が明確になる
- **事故防止**: アプリが誤ってスキーマ構造を変更するリスクを排除

### なぜ DEFAULT PRIVILEGES が必要か

- **新規オブジェクト対応**: マイグレーションで新しいテーブル/シーケンスを作成した直後も、アプリが即座に利用できる
- **権限エラー根絶**: 「テーブルは作れたのに SELECT できない」問題を防止
- **運用負荷削減**: オブジェクト作成のたびに手動で GRANT する必要がない

### なぜ SEQUENCE 権限が重要か

- **serial/identity対応**: `INSERT` 時に自動採番が動作するには `USAGE, SELECT` 権限が必須
- **頻発エラー**: `permission denied for sequence` が最も多い権限エラーの1つ

---

## 🎯 ロール設計

### ロール一覧

| ロール名 | LOGIN | 用途 | 権限レベル |
|---------|-------|------|----------|
| `sanbou_owner` | ❌ NOLOGIN | DBオブジェクトの所有者（owner専用） | スキーマ・テーブル・シーケンス等の所有権 |
| `sanbou_app_dev` | ✅ LOGIN | local_dev環境のアプリ接続ユーザー | 必要十分な権限（RW/RO） |
| `sanbou_app_stg` | ✅ LOGIN | vm_stg環境のアプリ接続ユーザー | 同上 |
| `sanbou_app_prod` | ✅ LOGIN | vm_prod環境のアプリ接続ユーザー | 同上 |
| `app_readonly` | ❌ NOLOGIN | 読み取り専用アクセス用（将来の拡張） | SELECT のみ |
| `myuser` | ✅ LOGIN (superuser) | 緊急用（break-glass） | superuser（使用は最小限に） |

### 環境ごとの変数

| 環境 | POSTGRES_USER | POSTGRES_DB | パスワード |
|------|---------------|-------------|-----------|
| local_dev | `sanbou_app_dev` | `sanbou_dev` | `.env.local_dev.secrets` |
| vm_stg | `sanbou_app_stg` | `sanbou_stg` | `.env.vm_stg.secrets` |
| vm_prod | `sanbou_app_prod` | `sanbou_prod` | `.env.vm_prod.secrets` |

---

## 🗂️ スキーマ別権限方針

| スキーマ | 用途 | owner | アプリ権限 | 備考 |
|---------|------|-------|----------|------|
| `raw` | 生データ保存 | `sanbou_owner` | **RW** (SELECT, INSERT, UPDATE, DELETE) + SEQUENCES | CSVアップロード先 |
| `stg` | 正規化済みデータ | `sanbou_owner` | **RW** + SEQUENCES | ETL処理の中間層 |
| `mart` | 集計・分析用 | `sanbou_owner` | **RO** (SELECT) | マテリアライズドビュー・集計テーブル |
| `ref` | マスタデータ | `sanbou_owner` | **RO** (SELECT) | 参照専用 |
| `kpi` | KPI管理 | `sanbou_owner` | **RW** + SEQUENCES | 月次目標等の更新が必要 |
| `log` | ログテーブル | `sanbou_owner` | **RW** + SEQUENCES | アプリログ記録 |
| `app` | アプリ固有機能 | `sanbou_owner` | **RW** + SEQUENCES | お知らせ機能等 |
| `app_auth` | 認証情報 | `sanbou_owner` | **RW** + SEQUENCES | 将来の認証機能用 |
| `forecast` | 予測データ | `sanbou_owner` | **RW** + SEQUENCES | AI予測結果保存 |
| `jobs` | ジョブ管理 | `sanbou_owner` | **RW** + SEQUENCES | バックグラウンドジョブ |
| `sandbox` | 開発用 | `sanbou_owner` | **RW** + SEQUENCES | 実験・検証用 |
| `public` | デフォルト | `sanbou_owner` | **RW** + SEQUENCES | alembic_version等 |

**凡例**:
- **RW**: SELECT, INSERT, UPDATE, DELETE
- **RO**: SELECT のみ
- **SEQUENCES**: USAGE, SELECT（自動採番に必須）

---

## 🚀 適用手順

### 事前準備（必須）

#### 1. バックアップ取得

```bash
# 環境を指定してバックアップ
make backup ENV=local_dev

# または直接実行
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  sh -c 'pg_dump -U "$POSTGRES_USER" -d "${POSTGRES_DB:-postgres}" -Fc' \
  > backups/sanbou_dev_$(date +%Y%m%d_%H%M%S).dump

# グローバル情報（ロール定義）もバックアップ
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  sh -c 'pg_dumpall -U "$POSTGRES_USER" --globals-only' \
  > backups/globals_$(date +%Y%m%d_%H%M%S).sql
```

#### 2. 環境確認

```bash
# 現在の状態を確認
make db-verify-ownership ENV=local_dev
```

### local_dev 環境での適用

```bash
# 1. ロール作成
make db-fix-ownership ENV=local_dev STEP=roles

# 2. 所有権移管
make db-fix-ownership ENV=local_dev STEP=reassign

# 3. 権限付与
make db-fix-ownership ENV=local_dev STEP=grants

# 4. デフォルト権限設定
make db-fix-ownership ENV=local_dev STEP=defaults

# 5. 検証
make db-verify-ownership ENV=local_dev

# または一括実行（推奨）
make db-fix-ownership ENV=local_dev
```

### vm_stg 環境での適用

⚠️ **ステージング環境で十分にテストしてから本番適用してください**

```bash
# VM内で実行
make db-fix-ownership ENV=vm_stg
```

### vm_prod 環境での適用

⚠️ **本番環境は必ずメンテナンス時間内に実施**

```bash
# 1. 事前バックアップ（必須）
make backup ENV=vm_prod

# 2. アプリ停止（影響を最小化）
make down ENV=vm_prod

# 3. 権限整備実行
make db-fix-ownership ENV=vm_prod

# 4. 検証
make db-verify-ownership ENV=vm_prod

# 5. アプリ起動
make up ENV=vm_prod

# 6. 動作確認
make health ENV=vm_prod
```

---

## 🔍 検証方法

### スクリプトによる自動検証

```bash
make db-verify-ownership ENV=local_dev
```

### 手動確認

```sql
-- スキーマ owner 確認
SELECT nspname, pg_catalog.pg_get_userbyid(nspowner) as owner
FROM pg_namespace
WHERE nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
ORDER BY nspname;

-- テーブル owner 確認
SELECT schemaname, tablename, tableowner
FROM pg_tables
WHERE schemaname IN ('raw', 'stg', 'mart', 'ref', 'kpi', 'log', 'app', 'app_auth', 'forecast', 'jobs', 'sandbox', 'public')
ORDER BY schemaname, tablename
LIMIT 20;

-- アプリユーザーの権限確認
SELECT 
  table_schema,
  privilege_type,
  COUNT(*) as count
FROM information_schema.table_privileges
WHERE grantee = current_user
  AND table_schema IN ('raw', 'stg', 'mart', 'ref', 'kpi', 'log', 'app')
GROUP BY table_schema, privilege_type
ORDER BY table_schema, privilege_type;
```

### 期待される出力

1. **スキーマ owner**: すべて `sanbou_owner`（system schema除く）
2. **テーブル owner**: すべて `sanbou_owner`
3. **アプリ権限**:
   - stg: SELECT, INSERT, UPDATE, DELETE
   - mart: SELECT
   - ref: SELECT
   - kpi: SELECT, INSERT, UPDATE, DELETE

---

## 🔄 ロールバック手順

### 軽微な問題（権限不足）の場合

```bash
# 権限だけ再適用
make db-fix-ownership ENV=local_dev STEP=grants
make db-fix-ownership ENV=local_dev STEP=defaults
```

### 深刻な問題の場合

```bash
# バックアップから復元
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  sh -c 'pg_restore -U "$POSTGRES_USER" -d "${POSTGRES_DB:-postgres}" \
         --clean --if-exists --no-owner --no-acl' \
  < backups/sanbou_dev_YYYYMMDD_HHMMSS.dump

# グローバル情報を復元（ロール定義）
cat backups/globals_YYYYMMDD_HHMMSS.sql | \
  docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  sh -c 'psql -U "$POSTGRES_USER" -d postgres'
```

---

## 📝 スクリプト一覧

| ファイル | 用途 | 冪等性 |
|---------|------|-------|
| `01_roles.sql` | sanbou_owner ロール作成 | ✅ |
| `02_reassign_ownership.sql` | 所有権を sanbou_owner に移管 | ✅ |
| `03_grants.sql` | アプリユーザーへ権限付与 | ✅ |
| `04_default_privileges.sql` | 新規オブジェクトへの自動権限設定 | ✅ |
| `99_verify.sql` | 検証クエリ | - |

---

## ⚠️ 注意事項

### local_dev 特有の設定

開発環境では利便性のため、以下を許可しています：

```sql
-- local_dev のみ: アプリユーザーが owner ロールを持つ
GRANT sanbou_owner TO sanbou_app_dev;
```

これにより、開発中にマイグレーションを直接実行できます。  
⚠️ **stg/prod では設定しない**

### myuser の扱い

- `myuser` は削除しません（break-glass 用）
- 日常運用では使用しません
- 緊急時のみ使用してください

### マイグレーション実行ユーザー

- **推奨**: `sanbou_owner` ロールを持つユーザーで実行
- **local_dev**: `sanbou_app_dev` でも可（GRANT sanbou_owner 済み）
- **stg/prod**: 専用の migrator ユーザーを作成するか、一時的に GRANT して実行

---

## 🔗 関連ファイル

- Makefile: [makefile](../../makefile)
- 環境変数: [env/](../../env/)
- Secrets: [secrets/](../../secrets/)
- Legacy Scripts: [ops/db/legacy/](legacy/) - 旧スクリプト（参照用）
- Development Tools: [scripts/db/](../../scripts/db/) - 開発用ツール（ダンプ等）

---

## 📚 参考資料

- [PostgreSQL: Privileges](https://www.postgresql.org/docs/current/ddl-priv.html)
- [PostgreSQL: Default Privileges](https://www.postgresql.org/docs/current/sql-alterdefaultprivileges.html)
- [PostgreSQL: Role Management](https://www.postgresql.org/docs/current/user-manag.html)

---

**作成者**: GitHub Copilot  
**レビュー**: -  
**承認**: -
