#!/usr/bin/env sh
# =============================================================
# print_pg_version_in_volume.sh
# 既存ボリューム内の PG_VERSION ファイルを読み取り、
# PostgreSQL のメジャーバージョンを確認します
# =============================================================
set -eu

VOLUME="${1:?Usage: $0 VOLUME_NAME}"

echo "[info] Reading PG_VERSION from volume: $VOLUME"

docker run --rm -v "$VOLUME:/var/lib/postgresql/data" busybox \
  sh -c 'cat /var/lib/postgresql/data/PG_VERSION'
