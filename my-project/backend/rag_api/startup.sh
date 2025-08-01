#!/bin/bash
set -e

gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
if [ $? -ne 0 ]; then
  echo "❌ GCPサービスアカウント認証に失敗しました"
  exit 1
fi
echo "✅ Authenticated with service account."

# GCSから構造化データをローカルにコピー
TARGET_DIR="/backend/app/local_data/master"

if [ "$(ls -A $TARGET_DIR 2>/dev/null)" ]; then
  echo "⏩ [1/2] Local data already exists. Skipping GCS download."
else
  echo "🌀 [1/2] Downloading structured data from GCS..."
  mkdir -p "$TARGET_DIR"
  if gsutil -m cp -r gs://object_haikibutu/master/* "$TARGET_DIR/"; then
    echo "✅ [1/2] GCS download complete."
  else
    echo "❌ [1/2] GCSからのデータ取得に失敗しました"
    exit 1
  fi
fi

# FastAPI起動
echo "🚀 [2/2] Starting FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
