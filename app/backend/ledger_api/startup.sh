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
else
    # 既定パスが存在しない / 読めない場合に secrets へフォールバック
    if [ ! -r "${GOOGLE_APPLICATION_CREDENTIALS}" ]; then
        echo "[WARN] GOOGLE_APPLICATION_CREDENTIALS is set but not readable: ${GOOGLE_APPLICATION_CREDENTIALS}" >&2
        if [ -f "/backend/secrets/${STAGE}-key.json" ]; then
            export GOOGLE_APPLICATION_CREDENTIALS="/backend/secrets/${STAGE}-key.json"
            echo "[INFO] fallback GOOGLE_APPLICATION_CREDENTIALS -> ${GOOGLE_APPLICATION_CREDENTIALS}"
        elif [ -f "/backend/secrets/key.json" ]; then
            export GOOGLE_APPLICATION_CREDENTIALS="/backend/secrets/key.json"
            echo "[INFO] fallback GOOGLE_APPLICATION_CREDENTIALS -> ${GOOGLE_APPLICATION_CREDENTIALS}"
        fi
    fi
fi

echo "[INFO] GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS:-<none>}"

## preflight ロジックは startup.py に統合済み

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
