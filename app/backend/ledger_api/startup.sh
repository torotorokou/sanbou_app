#!/bin/bash
set -eu

STAGE=${STAGE:-dev}
echo "[INFO] startup.sh stage=$STAGE"

# GCS関連の認証設定は不要（Git管理されたローカルファイルを使用）

# ------------------------------------------------------------
# Python startup 処理（ログ出力のみ）
# ------------------------------------------------------------
if python3 -m app.startup; then
    echo "[INFO] startup script succeeded"
else
    echo "[WARN] startup script failed (continuing)" >&2
fi


echo "[INFO] launching app: $*"
exec "$@"
