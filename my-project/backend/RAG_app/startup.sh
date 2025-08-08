#!/bin/bash
gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
echo "✅ Authenticated with service account."
# GCSから構造化データをローカルにコピー
if [ -d /app/local_data/master ]; then
  echo "⏩ [1/2] Local data already exists. Skipping GCS download."
else
  echo "🌀 [1/2] Downloading structured data from GCS..."
  gsutil -m cp -r gs://object_haikibutu/master /app/local_data/
  echo "✅ [1/2] GCS download complete."
fi
# FastAPI起動
echo "🚀 [2/2] Starting FastAPI..."
uvicorn app.main:app --host 0.0.0.0 --port 8000
# End of startup sc