# Database Permission Issues & Solutions

## Problem: API 500/503 Errors Due to Schema Access Permissions

### Symptoms
フロントエンドから以下のようなエラーが発生:
- `/core_api/calendar/month?year=2025&month=12` → 503 Service Unavailable
- `/core_api/dashboard/target?date=2025-12-01&mode=monthly` → 500 Internal Server Error
- `/core_api/inbound/daily?start=2025-12-01&end=2025-12-31` → 500 Internal Server Error

### Root Cause
PostgreSQL データベースで `myuser` が `ref` および `mart` スキーマへのアクセス権限を持っていない：
```
psycopg.errors.InsufficientPrivilege: permission denied for schema ref
psycopg.errors.InsufficientPrivilege: permission denied for schema mart
```

### Solution

#### 1. 即座の修正（手動実行）
```bash
# 権限設定スクリプトを実行
bash scripts/db/setup_permissions.sh

# または直接SQLを実行
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev << 'EOF'
GRANT USAGE ON SCHEMA ref TO myuser;
GRANT USAGE ON SCHEMA mart TO myuser;
GRANT SELECT ON ALL TABLES IN SCHEMA ref TO myuser;
GRANT SELECT ON ALL TABLES IN SCHEMA mart TO myuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA ref GRANT SELECT ON TABLES TO myuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA mart GRANT SELECT ON TABLES TO myuser;
EOF

# core_api を再起動して新しい権限を適用
docker compose -f docker/docker-compose.dev.yml -p local_dev restart core_api
```

#### 2. 永続的な修正（推奨）
マイグレーションスクリプトに権限付与を追加するか、データベース初期化時に自動実行されるようにします。

### Verification
```bash
# 権限を確認
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -c "\dp ref.*"

docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -c "\dp mart.*"
```

### Prevention
- データベースマイグレーション後は `scripts/db/setup_permissions.sh` を実行
- 新しいスキーマやテーブルを作成する場合は、権限付与を忘れずに
- `ALTER DEFAULT PRIVILEGES` により将来作成されるオブジェクトにも自動的に権限が付与される

## Related Files
- `/scripts/db/grant_schema_permissions.sql` - 権限付与SQLスクリプト
- `/scripts/db/setup_permissions.sh` - 権限設定実行スクリプト
