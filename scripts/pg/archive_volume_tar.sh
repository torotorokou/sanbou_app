#!/usr/bin/env sh
# =============================================================
# archive_volume_tar.sh
# 旧ボリュームの完全バックアップ（tar.gz）を作成します
# 出力先: backups/pg/volume_${VOLUME}_${TIMESTAMP}.tgz
# =============================================================
set -eu

VOLUME="${1:?Usage: $0 VOLUME_NAME}"
TS="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="backups/pg"

mkdir -p "$BACKUP_DIR"

echo "[info] Archiving volume: $VOLUME"
echo "[info] Output: ${BACKUP_DIR}/volume_${VOLUME}_${TS}.tgz"

docker run --rm -v "$VOLUME:/data:ro" -w /data busybox \
  sh -c "tar -czf - ." > "${BACKUP_DIR}/volume_${VOLUME}_${TS}.tgz"

echo "[ok] Saved: ${BACKUP_DIR}/volume_${VOLUME}_${TS}.tgz"
ls -lh "${BACKUP_DIR}/volume_${VOLUME}_${TS}.tgz"
