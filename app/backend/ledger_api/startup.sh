#!/bin/bash
set -eu

STAGE=${STAGE:-dev}
echo "[INFO] startup.sh stage=$STAGE"

# 環境毎の service account key 探索
if [ -z "${GOOGLE_APPLICATION_CREDENTIALS:-}" ]; then
    if [ -f "/backend/secrets/${STAGE}-key.json" ]; then
        export GOOGLE_APPLICATION_CREDENTIALS="/backend/secrets/${STAGE}-key.json"
    elif [ -f "/backend/secrets/key.json" ]; then
        export GOOGLE_APPLICATION_CREDENTIALS="/backend/secrets/key.json"
    fi
fi

echo "[INFO] GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS:-<none>}"

# ------------------------------------------------------------
# STRICT_STARTUP=true の場合: Python preflight を実行
# ------------------------------------------------------------
if [ "${STRICT_STARTUP:-false}" = "true" ]; then
    echo "[INFO] STRICT_STARTUP enabled: running GCS preflight"
    python3 /backend/startup_preflight.py
fi

# ------------------------------------------------------------
# Python startup 処理 (例: GCS からの同期など)
# ------------------------------------------------------------
if python3 -m app.startup; then
    echo "[INFO] startup script succeeded"
else
    if [ "${STRICT_STARTUP:-false}" = "true" ]; then
        echo "[ERROR] startup script failed (STRICT_STARTUP)" >&2
        exit 100
    else
        echo "[WARN] startup script failed (continuing)" >&2
    fi
fi

echo "[INFO] launching app: $*"
exec "$@"
