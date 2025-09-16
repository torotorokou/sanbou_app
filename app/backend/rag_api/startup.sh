
#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

# --- 環境・基底パス ---
STAGE=${STAGE:-dev}
# APP_ROOT_DIR (新) -> APP_BASE_DIR (旧) -> /backend の順で基底パス決定
_BASE_DIR="${APP_ROOT_DIR:-${APP_BASE_DIR:-/backend}}"
# /backend が書き込み不可な場合はホームへフォールバック
TARGET_DIR_DEFAULT="${_BASE_DIR}/local_data/master"
TARGET_DIR="${TARGET_DIR:-$TARGET_DIR_DEFAULT}"
# root 権限で作成し所有権付与 (コンテナは appuser 実行)
if mkdir -p "${TARGET_DIR%/master}" 2>/dev/null; then
  :
else
  # /backend に書けない場合はホームへフォールバック
  TARGET_DIR="/home/appuser/local_data/master"
  mkdir -p "${TARGET_DIR%/master}" || true
fi
if command -v chown >/dev/null 2>&1; then
  chown -R appuser:appuser "${TARGET_DIR%/master}" 2>/dev/null || true
fi
# --- GCS 取得元（環境別ディレクトリ構成） ---
# 既存の環境変数で明示されていれば尊重。未設定時は STAGE から自動決定。
# 例: gs://sanbouapp-stg/ledger_api/rag_api/object_haikibutu/*
if [ -z "${GCS_BUCKET_NAME:-}" ]; then
  GCS_BUCKET_NAME="sanbouapp-${STAGE}"
fi
if [ -z "${GCS_DATA_PREFIX:-}" ]; then
  GCS_DATA_PREFIX="ledger_api/rag_api/object_haikibutu"
fi

# --- GOOGLE_APPLICATION_CREDENTIALS 解決 (ledger_api と同様の方針) ---
# 既に外部から与えられている場合は尊重。ただし読めない場合はフォールバック。
if [ -z "${GOOGLE_APPLICATION_CREDENTIALS:-}" ]; then
  if [ -f "/run/secrets/rag_gcs_key.json" ]; then
    export GOOGLE_APPLICATION_CREDENTIALS="/run/secrets/rag_gcs_key.json"
  elif [ -f "/backend/secrets/${STAGE}_key.json" ]; then
    export GOOGLE_APPLICATION_CREDENTIALS="/backend/secrets/${STAGE}_key.json"
  elif [ -f "/backend/secrets/${STAGE}-key.json" ]; then
    export GOOGLE_APPLICATION_CREDENTIALS="/backend/secrets/${STAGE}-key.json"
  elif [ -f "/backend/secrets/key.json" ]; then
    export GOOGLE_APPLICATION_CREDENTIALS="/backend/secrets/key.json"
  else
    GOOGLE_APPLICATION_CREDENTIALS="/root/.config/gcloud/application_default_credentials.json"
  fi
else
  if [ ! -r "${GOOGLE_APPLICATION_CREDENTIALS}" ]; then
    echo "[WARN] GOOGLE_APPLICATION_CREDENTIALS is set but not readable: ${GOOGLE_APPLICATION_CREDENTIALS}" >&2
    if [ -f "/run/secrets/rag_gcs_key.json" ]; then
      export GOOGLE_APPLICATION_CREDENTIALS="/run/secrets/rag_gcs_key.json"
      echo "[INFO] fallback GOOGLE_APPLICATIONS_CREDENTIALS -> ${GOOGLE_APPLICATION_CREDENTIALS}"
    elif [ -f "/backend/secrets/${STAGE}_key.json" ]; then
      export GOOGLE_APPLICATION_CREDENTIALS="/backend/secrets/${STAGE}_key.json"
      echo "[INFO] fallback GOOGLE_APPLICATIONS_CREDENTIALS -> ${GOOGLE_APPLICATION_CREDENTIALS}"
    elif [ -f "/backend/secrets/${STAGE}-key.json" ]; then
      export GOOGLE_APPLICATION_CREDENTIALS="/backend/secrets/${STAGE}-key.json"
      echo "[INFO] fallback GOOGLE_APPLICATIONS_CREDENTIALS -> ${GOOGLE_APPLICATION_CREDENTIALS}"
    elif [ -f "/backend/secrets/key.json" ]; then
      export GOOGLE_APPLICATION_CREDENTIALS="/backend/secrets/key.json"
      echo "[INFO] fallback GOOGLE_APPLICATIONS_CREDENTIALS -> ${GOOGLE_APPLICATION_CREDENTIALS}"
    fi
  fi
fi
echo "[INFO] GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS:-<none>}"

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

# --- GCP認証 (スキップ条件付き) ---
SKIP_GCS="${SKIP_GCS:-0}"
if [[ "$SKIP_GCS" == "1" ]]; then
  echo "⚠️  SKIP_GCS=1 が指定されたため GCS 処理をスキップします。"
else
  if ! command -v gcloud >/dev/null 2>&1 || ! command -v gsutil >/dev/null 2>&1; then
    echo "⚠️  gcloud/gsutil が見つからないため GCS 処理をスキップします。" >&2
    SKIP_GCS=1
  elif [[ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]]; then
    echo "⚠️  認証ファイル $GOOGLE_APPLICATION_CREDENTIALS が無いため GCS 処理をスキップします。" >&2
    SKIP_GCS=1
  fi
  if [[ "$SKIP_GCS" != "1" ]]; then
    if gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"; then
      echo "✅ Authenticated with service account."
    # サービスアカウント確認
    SA_EMAIL=$(grep -o '"client_email" *: *"[^"]\+"' "$GOOGLE_APPLICATION_CREDENTIALS" | cut -d'"' -f4 || true)
    echo "Using service account: ${SA_EMAIL}"
    else
      echo "⚠️  サービスアカウント認証に失敗。GCS 処理をスキップします。" >&2
      SKIP_GCS=1
    fi
  fi
fi

# --- データ取得（拡張ポイント：他データ種別もここで追加可能） ---
if [[ "$SKIP_GCS" == "1" ]]; then
  echo "⏩ [GCS] スキップ指定のためダウンロード無しで続行します。"
else
  if [ -n "$(ls -A "$TARGET_DIR" 2>/dev/null || true)" ]; then
    echo "⏩ [1/2] Local data already exists. Skipping GCS download."
  else
    if ! download_gcs_data "$GCS_BUCKET_NAME" "$GCS_DATA_PREFIX" "$TARGET_DIR"; then
      echo "⚠️  ダウンロード失敗しましたが起動は継続します。" >&2
      echo "ヒント: サービスアカウントに 'storage.objects.list' と 'storage.objects.get' 権限 (Storage Object Viewer など) が付与されているか確認してください。" >&2
    fi
  fi
fi

# --- FastAPI起動 ---
echo "APP_ROOT_DIR: ${APP_ROOT_DIR:-未設定} (fallback APP_BASE_DIR=${APP_BASE_DIR:-未設定})"
echo "🚀 [2/2] Starting FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000