# DB Schema Permissions Fix (2024-12-04)

## 問題の概要

フロントエンドからcore_apiへのリクエストが503/500エラーで失敗していた。

### エラーログ

```
permission denied for schema ref
permission denied for schema mart
```

### 影響範囲

- `/core_api/calendar/month` → 503エラー
- `/core_api/inbound/daily` → 500エラー
- `/core_api/dashboard/target` → 500エラー

## 根本原因

**PostgreSQLのスキーマ権限が不足**していた。

### 詳細

1. DBスキーマの所有者: `dbuser`
2. アプリケーションのDBユーザー: `sanbou_app_dev`
3. `sanbou_app_dev`ユーザーが以下のスキーマにアクセスできなかった:
   - `ref` (カレンダーマスタデータ)
   - `mart` (集計ビュー・マテリアライズドビュー)
   - その他のスキーマ(`app_auth`, `forecast`, `kpi`, `log`, `raw`, `stg`, `sandbox`)

### なぜ発生したか

- データベース初期化時に`dbuser`でスキーマを作成
- アプリケーション用ユーザー`sanbou_app_dev`への権限付与が漏れていた
- `DATABASE_URL`は`sanbou_app_dev`を使用していたが、権限が未設定

## 修正内容

### 1. 権限修正スクリプトの作成

**ファイル**: `scripts/db/fix_schema_permissions.sql`

以下の権限を`sanbou_app_dev`ユーザーに付与:

#### スキーマレベル権限

```sql
GRANT USAGE ON SCHEMA <schema_name> TO sanbou_app_dev;
```

#### テーブル/ビュー権限

- **読み取り専用スキーマ** (`ref`, `mart`, `app_auth`, `forecast`, `kpi`):
  - `SELECT` 権限のみ
- **読み書きスキーマ** (`raw`, `stg`, `log`, `sandbox`, `public`):
  - `SELECT, INSERT, UPDATE, DELETE` 権限

#### シーケンス権限

```sql
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA <schema_name> TO sanbou_app_dev;
```

#### デフォルト権限（将来のオブジェクト用）

```sql
ALTER DEFAULT PRIVILEGES FOR ROLE dbuser IN SCHEMA <schema_name>
  GRANT SELECT ON TABLES TO sanbou_app_dev;
```

### 2. 実行コマンド

```bash
docker compose -f docker/docker-compose.dev.yml -p local_dev \
  exec -T db psql -U dbuser -d sanbou_dev \
  -f - < scripts/db/fix_schema_permissions.sql
```

### 3. 検証

```bash
# ビューへのアクセステスト
docker compose -f docker/docker-compose.dev.yml -p local_dev \
  exec -T db psql -U sanbou_app_dev -d sanbou_dev \
  -c "SELECT * FROM ref.v_calendar_classified LIMIT 5;"

# APIエンドポイントテスト
curl "http://localhost:8003/core_api/calendar/month?year=2025&month=12"
curl "http://localhost:8003/core_api/inbound/daily?start=2025-12-01&end=2025-12-31&cum_scope=month"
curl "http://localhost:8003/core_api/dashboard/target?date=2025-12-01&mode=monthly"
```

すべて正常に動作することを確認。

## 今後の対策

### 1. DB初期化スクリプトの改善

データベース初期化時に以下を自動実行するよう改善が必要:

- アプリケーション用ユーザーの作成
- 必要な権限の付与
- デフォルト権限の設定

### 2. 権限チェック自動化

ヘルスチェックや起動時に以下を確認:

```python
# 例: 起動時チェック
required_schemas = ['ref', 'mart', 'raw', 'stg']
for schema in required_schemas:
    result = db.execute(f"SELECT has_schema_privilege(current_user, '{schema}', 'USAGE')")
    if not result:
        logger.error(f"Missing permission for schema: {schema}")
```

### 3. ドキュメント整備

- `scripts/db/README.md` に権限管理の手順を明記
- 新規環境構築時のチェックリストに権限設定を追加

## 関連ファイル

- `scripts/db/fix_schema_permissions.sql` - 権限修正スクリプト（新規作成）
- `secrets/.env.local_dev.secrets` - DATABASE_URLの設定
- `docker/docker-compose.dev.yml` - DB接続設定

## 参考情報

### PostgreSQL権限の階層

1. データベースレベル: `CONNECT`
2. スキーマレベル: `USAGE`
3. オブジェクトレベル: `SELECT`, `INSERT`, `UPDATE`, `DELETE`

すべてのレベルで権限が必要。

### 権限確認クエリ

```sql
-- スキーマへのUSAGE権限確認
SELECT nspname, has_schema_privilege('sanbou_app_dev', nspname, 'USAGE')
FROM pg_namespace
WHERE nspname NOT LIKE 'pg_%' AND nspname != 'information_schema';

-- テーブルへのSELECT権限確認
SELECT schemaname, tablename,
       has_table_privilege('sanbou_app_dev', schemaname||'.'||tablename, 'SELECT')
FROM pg_tables
WHERE schemaname = 'ref';
```

## タイムライン

- **2024-12-04 14:40** - フロントエンドでAPI エラー発生を確認
- **2024-12-04 14:41** - core_apiログで`permission denied for schema ref`を特定
- **2024-12-04 14:42** - ブランチ`fix/db-schema-permissions`作成
- **2024-12-04 14:43** - 権限修正スクリプト作成・実行
- **2024-12-04 14:44** - core_api再起動、APIテスト完了
- **2024-12-04 14:45** - 修正完了、ドキュメント作成
