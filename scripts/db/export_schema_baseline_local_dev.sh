#!/usr/bin/env bash
# ============================================================================
# scripts/db/export_schema_baseline_local_dev.sh
# ============================================================================
# 目的:
#   local_dev の現在のスキーマ（head時点）を schema_baseline.sql として
#   エクスポートする。v2 Alembic の起点として使用。
#
# 使い方:
#   ./scripts/db/export_schema_baseline_local_dev.sh
#
# 出力:
#   app/backend/core_api/migrations_v2/sql/schema_baseline.sql
#
# 前提条件:
#   - local_dev 環境が起動していること (make up ENV=local_dev)
#   - Alembic が head まで適用済みであること (make al-up ENV=local_dev)
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

COMPOSE_FILE="docker/docker-compose.dev.yml"
PROJECT_NAME="local_dev"
DB_SERVICE="db"
PGUSER="myuser"
PGDB="sanbou_dev"

OUTPUT_FILE="app/backend/core_api/migrations_v2/sql/schema_baseline.sql"

echo "========================================"
echo "Schema Baseline Export (local_dev)"
echo "========================================"
echo ""
echo "Source DB: $PGDB"
echo "Output: $OUTPUT_FILE"
echo ""

# 出力先ディレクトリ作成（存在しない場合）
mkdir -p "$(dirname "$REPO_ROOT/$OUTPUT_FILE")"

# pg_dump 実行
echo "[1/2] Dumping schema (--schema-only, no ownership/privileges)..."
docker compose -f "$REPO_ROOT/$COMPOSE_FILE" -p "$PROJECT_NAME" exec -T "$DB_SERVICE" \
  pg_dump -U "$PGUSER" -d "$PGDB" \
    --schema-only \
    --no-owner \
    --no-privileges \
    --no-tablespaces \
    --no-security-labels \
    --no-comments \
  > "$REPO_ROOT/$OUTPUT_FILE"

echo "[2/2] Schema exported successfully!"
echo ""
echo "File size:"
wc -l "$REPO_ROOT/$OUTPUT_FILE"
echo ""
echo "First 10 lines:"
head -10 "$REPO_ROOT/$OUTPUT_FILE"
echo ""
echo "✅ Done. You can now commit this file:"
echo "   git add $OUTPUT_FILE"
echo "   git commit -m 'Add schema baseline for Alembic v2'"
