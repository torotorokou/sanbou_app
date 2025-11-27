#!/usr/bin/env sh
# =============================================================
# restore_to_v17.sh
# v17 へ pg_dumpall の SQL をリストアします
# 接続情報は環境変数から取得（PGHOST, PGPORT, PGUSER, PGDATABASE, PGPASSWORD）
# =============================================================
set -eu

SQL="${1:?Usage: $0 PATH_TO_SQL}"

# デフォルト値
HOST="${PGHOST:-localhost}"
PORT="${PGPORT:-5432}"
USER="${PGUSER:-postgres}"
DB="${PGDATABASE:-postgres}"

# PGPASSWORD は環境変数で設定済みの前提（セキュリティ考慮）
if [ -z "${PGPASSWORD:-}" ]; then
  echo "[warn] PGPASSWORD is not set. You may be prompted for password."
fi

echo "[info] Restoring SQL to PostgreSQL 17"
echo "[info] Host: ${HOST}:${PORT}, User: ${USER}, DB: ${DB}"
echo "[info] SQL file: ${SQL}"

# psql でリストア
psql "host=${HOST} port=${PORT} user=${USER} dbname=${DB}" < "${SQL}"

echo "[ok] Restore completed"
