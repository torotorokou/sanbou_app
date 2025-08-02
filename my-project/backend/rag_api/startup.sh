
#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

# --- 設定値（環境変数で上書き可能） ---
GCS_BUCKET_NAME="${GCS_BUCKET_NAME:-object_haikibutu}"
GCS_DATA_PREFIX="${GCS_DATA_PREFIX:-master}"
TARGET_DIR="${TARGET_DIR:-/app/local_data/master}"
GOOGLE_APPLICATION_CREDENTIALS="${GOOGLE_APPLICATION_CREDENTIALS:-/root/.config/gcloud/application_default_credentials.json}"

# --- 関数化：GCSからデータ取得 ---
download_gcs_data() {
  local bucket="$1"
  local prefix="$2"
  local target_dir="$3"
  echo "🌀 [GCS] Downloading gs://$bucket/$prefix/* → $target_dir"
  mkdir -p "$target_dir"
  if gsutil -m cp -r "gs://$bucket/$prefix/*" "$target_dir/"; then
    echo "✅ [GCS] Download complete."
    return 0
  else
    echo "❌ [GCS] データ取得に失敗しました (gs://$bucket/$prefix/*)" >&2
    return 1
  fi
}

# --- GCP認証 ---
if ! gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"; then
  echo "❌ GCPサービスアカウント認証に失敗しました" >&2
  exit 10
fi
echo "✅ Authenticated with service account."

# --- データ取得（拡張ポイント：他データ種別もここで追加可能） ---
if [ -n "$(ls -A "$TARGET_DIR" 2>/dev/null || true)" ]; then
  echo "⏩ [1/2] Local data already exists. Skipping GCS download."
else
  if ! download_gcs_data "$GCS_BUCKET_NAME" "$GCS_DATA_PREFIX" "$TARGET_DIR"; then
    exit 20
  fi
fi

# --- FastAPI起動 ---
echo "🚀 [2/2] Starting FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
