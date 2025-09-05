#!/bin/bash
set -eu

STAGE=${STAGE:-dev}
echo "[INFO] startup.sh stage=$STAGE"

# 環境毎の service account key (ホスト側でマウントされている前提) を探索
# 既定パス優先順位: /backend/secrets/${STAGE}-key.json -> /backend/secrets/key.json
if [ -z "${GOOGLE_APPLICATION_CREDENTIALS:-}" ]; then
	if [ -f "/backend/secrets/${STAGE}-key.json" ]; then
		export GOOGLE_APPLICATION_CREDENTIALS="/backend/secrets/${STAGE}-key.json"
	elif [ -f "/backend/secrets/key.json" ]; then
		export GOOGLE_APPLICATION_CREDENTIALS="/backend/secrets/key.json"
	fi
fi

echo "[INFO] GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS:-<none>}"

# Python の startup 処理 (GCS 同期等)
python -m app.startup || echo "[WARN] startup script failed (continuing)"

echo "[INFO] launching app: $*"
exec "$@"
