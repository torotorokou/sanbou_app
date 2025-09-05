#!/bin/bash
set -eu

STAGE=${STAGE:-dev}
echo "[INFO] startup.sh stage=$STAGE"

# 環境毎の service account key (ホスト側でマウントされている前提) を探索
# 優先順位: 明示 env > /backend/secrets/${STAGE}-key.json > /backend/secrets/key.json
if [ -z "${GOOGLE_APPLICATION_CREDENTIALS:-}" ]; then
	if [ -f "/backend/secrets/${STAGE}-key.json" ]; then
		export GOOGLE_APPLICATION_CREDENTIALS="/backend/secrets/${STAGE}-key.json"
	elif [ -f "/backend/secrets/key.json" ]; then
		export GOOGLE_APPLICATION_CREDENTIALS="/backend/secrets/key.json"
	fi
fi

echo "[INFO] GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS:-<none>}"

# ------------------------------------------------------------
# STRICT_STARTUP=true の場合: GCS への read (bucket exists, list_blobs)
# をプリフライトし失敗なら即座に EXIT する (再発防止: 権限欠如で静かに起動しない)
# 環境変数:
#   STRICT_STARTUP=true で強制
#   GCS_BUCKET_NAME (未指定なら sanbouapp-stg をデフォルト利用)
# ------------------------------------------------------------
if [ "${STRICT_STARTUP:-false}" = "true" ]; then
	echo "[INFO] STRICT_STARTUP enabled: running GCS preflight"
	python3 - <<'PY'
import os, sys, json
from pathlib import Path
try:
		from google.cloud import storage  # type: ignore
except Exception as e:
		print('[ERROR] google-cloud-storage import failed:', e)
		sys.exit(90)

cred = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
if not cred or not Path(cred).is_file():
		print('[ERROR] key file missing:', cred)
		sys.exit(91)

try:
		ce = json.load(open(cred)).get('client_email')
		print('[INFO] key client_email:', ce)
except Exception as e:
		print('[ERROR] parse key failed:', e)
		sys.exit(92)

bucket_name = os.environ.get('GCS_BUCKET_NAME', 'sanbouapp-stg')
print('[INFO] target bucket:', bucket_name)

client = storage.Client()
bucket = client.bucket(bucket_name)
if not bucket.exists():
		print('[ERROR] bucket not accessible (exists()=False):', bucket_name)
		sys.exit(93)
print('[INFO] bucket exists OK')

try:
		it = client.list_blobs(bucket_name, max_results=1)
		next(iter(it), None)
		print('[INFO] list_blobs OK')
except Exception as e:
		print('[ERROR] list_blobs failed:', e)
		sys.exit(94)

print('[INFO] GCS preflight success')
PY
fi

# ------------------------------------------------------------
# Python startup 処理 (例: GCS からの同期など)。失敗時ポリシー:
#  - STRICT_STARTUP=true -> 異常終了
#  - それ以外 -> WARN ログのみ継続
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
