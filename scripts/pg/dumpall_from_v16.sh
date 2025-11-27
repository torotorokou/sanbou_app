#!/usr/bin/env sh
# =============================================================
# dumpall_from_v16.sh
# v15/v16 クラスタから全DB論理ダンプ（pg_dumpall）を取得します
# 一時的に postgres コンテナを起動 → ダンプ → 停止
# 出力先: backups/pg/pg_dumpall_${TIMESTAMP}.sql
# =============================================================
set -eu

VOLUME="${1:?Usage: $0 OLD_VOLUME_NAME}"
PG_VERSION="${2:-15}"
CONTAINER="pg${PG_VERSION}tmp_$$"
PORT="${PG_TEMP_PORT:-55432}"
BACKUP_DIR="backups/pg"

mkdir -p "$BACKUP_DIR"
TS="$(date +%Y%m%d_%H%M%S)"

echo "[info] Starting temporary postgres:${PG_VERSION} container..."
docker run -d --rm --name "$CONTAINER" \
  -v "$VOLUME:/var/lib/postgresql/data:ro" \
  -p "${PORT}:5432" \
  postgres:${PG_VERSION}-alpine

# 待機（pg_isready でヘルスチェック）
echo "[info] Waiting for PostgreSQL to be ready..."
until docker exec "$CONTAINER" pg_isready -U postgres >/dev/null 2>&1; do
  printf "."
  sleep 1
done
echo ""
echo "[ok] PostgreSQL is ready"

# pg_dumpall 実行
echo "[info] Running pg_dumpall..."
docker exec "$CONTAINER" sh -c "pg_dumpall -U postgres" \
  > "${BACKUP_DIR}/pg_dumpall_${TS}.sql"

# コンテナ停止
echo "[info] Stopping temporary container..."
docker stop "$CONTAINER" >/dev/null 2>&1 || true

echo "[ok] Saved: ${BACKUP_DIR}/pg_dumpall_${TS}.sql"
ls -lh "${BACKUP_DIR}/pg_dumpall_${TS}.sql"
