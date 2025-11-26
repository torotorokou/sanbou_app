#!/usr/bin/env bash
# =============================================================================
# dump_schema_current.sh
# PostgreSQL スキーマ全体を sql_current/schema_head.sql にダンプ
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# =============================================================================
# 設定値（環境変数で上書き可能）
# =============================================================================
ENV="${ENV:-local_dev}"
PGUSER="${PGUSER:-myuser}"
PGDB="${PGDB:-sanbou_dev}"
PG_SERVICE="${PG_SERVICE:-db}"

# Docker Compose 設定
if [[ "$ENV" == "local_dev" ]]; then
    COMPOSE_FILE="docker/docker-compose.dev.yml"
elif [[ "$ENV" == "local_stg" ]]; then
    COMPOSE_FILE="docker/docker-compose.stg.yml"
else
    echo "[error] Unsupported ENV: $ENV (supported: local_dev, local_stg)"
    exit 1
fi

DC="docker compose -f $COMPOSE_FILE -p $ENV"

# 出力先パス
OUTPUT_FILE="$PROJECT_ROOT/app/backend/core_api/migrations/alembic/sql_current/schema_head.sql"
OUTPUT_DIR="$(dirname "$OUTPUT_FILE")"

# =============================================================================
# メイン処理
# =============================================================================
echo "========================================="
echo " PostgreSQL Schema Dump"
echo "========================================="
echo "ENV:        $ENV"
echo "PGUSER:     $PGUSER"
echo "PGDB:       $PGDB"
echo "OUTPUT:     $OUTPUT_FILE"
echo "========================================="
echo ""

# 出力ディレクトリ確認
if [[ ! -d "$OUTPUT_DIR" ]]; then
    echo "[error] Output directory does not exist: $OUTPUT_DIR"
    exit 1
fi

# DB コンテナが起動しているか確認
if ! $DC ps --services --filter "status=running" | grep -q "^${PG_SERVICE}$"; then
    echo "[error] Database container '${PG_SERVICE}' is not running."
    echo "        Run 'make up ENV=$ENV' first."
    exit 1
fi

echo "[info] Dumping schema from ${PG_SERVICE}..."

# pg_dump でスキーマのみをダンプ
$DC exec -T "$PG_SERVICE" pg_dump \
    -U "$PGUSER" \
    -d "$PGDB" \
    --schema-only \
    --no-owner \
    --no-privileges \
    --no-tablespaces \
    > "$OUTPUT_FILE"

echo ""
echo "[ok] Schema dumped successfully!"
echo ""
echo "File: $OUTPUT_FILE"
echo "Size: $(du -h "$OUTPUT_FILE" | cut -f1)"
echo ""
echo "========================================="
echo " Next Steps"
echo "========================================="
echo "1. Review the generated schema_head.sql"
echo "2. Commit to git: git add sql_current/schema_head.sql"
echo "3. Document any schema changes in your PR"
echo ""
