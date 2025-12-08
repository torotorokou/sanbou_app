
#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

# =============================================================================
# RAG API スタートアップスクリプト - ADC (Application Default Credentials) 対応版
# =============================================================================
# 
# 認証方式:
#   - ローカル開発環境: gcloud auth application-default login による ADC
#   - GCE (stg/prod): VM にアタッチされたサービスアカウントによる ADC
#   - JSON キーファイルは使用しません
#
# =============================================================================

# --- 設定値（環境変数で上書き可能） ---
RAG_GCS_URI="${RAG_GCS_URI:-}"
GCS_BUCKET_NAME="${GCS_BUCKET_NAME:-object_haikibutu}"
GCS_DATA_PREFIX="${GCS_DATA_PREFIX:-master}"
_BASE_DIR="${APP_ROOT_DIR:-${APP_BASE_DIR:-/backend}}"
TARGET_DIR_DEFAULT="${_BASE_DIR}/local_data/master"
TARGET_DIR="${TARGET_DIR:-$TARGET_DIR_DEFAULT}"
STAGE=${STAGE:-dev}

# ターゲットディレクトリ作成
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

echo "[INFO] STAGE=$STAGE (ADC認証を使用)"
echo "[INFO] TARGET_DIR=$TARGET_DIR"

# --- 関数化：GCSからデータ取得 ---
download_gcs_data() {
  local bucket="$1"
  local prefix="$2"
  local target_dir="$3"
  local uri="$4"  # オプション: 完全URI
  mkdir -p "$target_dir"

  if [ -n "$uri" ]; then
    # 正規化: 末尾のスラッシュを除去
    local norm_uri="${uri%/}"
    echo "🌀 [GCS] Downloading ${norm_uri}/* → $target_dir"
    if gsutil -m cp -r "${norm_uri}/*" "$target_dir/" 2>&1; then
      echo "✅ [GCS] Download complete."
      return 0
    else
      local exit_code=$?
      echo "❌ [GCS] データ取得に失敗しました (${norm_uri}/*)" >&2
      echo "   終了コード: $exit_code" >&2
      
      # エラーの種類を推測
      if [ $exit_code -eq 1 ]; then
        echo "   🛑 可能性: 認証エラー、または権限不足 (403 Forbidden)" >&2
        echo "      - ADC認証が正しく設定されているか確認してください" >&2
        echo "      - サービスアカウントに 'Storage Object Viewer' ロールが付与されているか確認してください" >&2
      elif [ $exit_code -eq 3 ]; then
        echo "   🛑 可能性: バケットまたはオブジェクトが存在しない (404 NotFound)" >&2
        echo "      - バケット名やオブジェクトパスが正しいか確認してください" >&2
      else
        echo "   🛑 可能性: ネットワークエラー、またはその他のエラー" >&2
      fi
      
      return 1
    fi
  else
    echo "🌀 [GCS] Downloading gs://$bucket/$prefix/* → $target_dir"
    if gsutil -m cp -r "gs://$bucket/$prefix/*" "$target_dir/" 2>&1; then
      echo "✅ [GCS] Download complete."
      return 0
    else
      local exit_code=$?
      echo "❌ [GCS] データ取得に失敗しました (gs://$bucket/$prefix/*)" >&2
      echo "   終了コード: $exit_code" >&2
      
      # エラーの種類を推測
      if [ $exit_code -eq 1 ]; then
        echo "   🛑 可能性: 認証エラー、または権限不足 (403 Forbidden)" >&2
        echo "      - ADC認証が正しく設定されているか確認してください" >&2
        echo "      - サービスアカウントに 'Storage Object Viewer' ロールが付与されているか確認してください" >&2
        echo "      - STAGE=$STAGE, BUCKET=$bucket, PREFIX=$prefix" >&2
      elif [ $exit_code -eq 3 ]; then
        echo "   🛑 可能性: バケットまたはオブジェクトが存在しない (404 NotFound)" >&2
        echo "      - バケット名やオブジェクトパスが正しいか確認してください" >&2
        echo "      - BUCKET=$bucket, PREFIX=$prefix" >&2
      else
        echo "   🛑 可能性: ネットワークエラー、またはその他のエラー" >&2
      fi
      
      return 1
    fi
  fi
}

# --- GCP認証確認 (ADC使用) ---
SKIP_GCS="${SKIP_GCS:-0}"
if [[ "$SKIP_GCS" == "1" ]]; then
  echo "⚠️  SKIP_GCS=1 が指定されたため GCS 処理をスキップします。"
else
  if ! command -v gcloud >/dev/null 2>&1 || ! command -v gsutil >/dev/null 2>&1; then
    echo "⚠️  gcloud/gsutil が見つからないため GCS 処理をスキップします。" >&2
    SKIP_GCS=1
  else
    # ADCを使用してgcloudを初期化（JSONキー不要）
    echo "🔑 ADC (Application Default Credentials) を使用してGCPに接続します"
    echo "   STAGE=$STAGE"
    echo "   TARGET_DIR=$TARGET_DIR"
    
    # gcloud config list で認証状態を確認
    if gcloud config list 2>/dev/null | grep -q "account"; then
      echo "✅ GCP ADC認証確認完了 - gcloud config list にアカウント情報が存在"
      
      # 可能であればアカウント情報を表示
      if gcloud config list account 2>/dev/null; then
        echo "   使用中のアカウント情報を確認できました"
      fi
    else
      echo "⚠️  ADC認証が設定されていない可能性があります。GCS処理をスキップします。" >&2
      echo "   gcloud config list の出力を確認してください:" >&2
      gcloud config list 2>&1 | head -10 >&2
      echo "ヒント: ローカル開発の場合は 'gcloud auth application-default login' を実行してください" >&2
      echo "       GCE/Cloud Run の場合は、サービスアカウントがVMにアタッチされているか確認してください" >&2
      SKIP_GCS=1
    fi
  fi
fi

# --- データ取得（拡張ポイント：他データ種別もここで追加可能） ---
if [[ "$SKIP_GCS" == "1" ]]; then
  echo "⏩ [GCS] スキップ指定のためダウンロード無しで続行します。"
else
  # 実際のデータファイル（CSV/JSON/Parquet等）が存在するかチェック
  # readme.md や .gitkeep などのドキュメントファイルのみの場合はダウンロードを実行
  DATA_FILE_COUNT=$(find "$TARGET_DIR" -type f \( -name "*.csv" -o -name "*.json" -o -name "*.parquet" -o -name "*.jsonl" \) 2>/dev/null | wc -l)
  
  if [ "$DATA_FILE_COUNT" -gt 0 ]; then
    echo "⏩ [1/2] Local data already exists ($DATA_FILE_COUNT data files found). Skipping GCS download."
  else
    echo "📥 [1/2] No data files found in $TARGET_DIR. Downloading from GCS..."
    if ! download_gcs_data "$GCS_BUCKET_NAME" "$GCS_DATA_PREFIX" "$TARGET_DIR" "$RAG_GCS_URI"; then
      echo "⚠️  ダウンロード失敗しましたが起動は継続します。" >&2
      echo "ヒント:" >&2
      echo "  - ローカル: gcloud auth application-default login を実行してください" >&2
      echo "  - GCE: VM のサービスアカウントに Storage Object Viewer ロールが必要です" >&2
    fi
  fi
fi

# --- FastAPI起動 ---
echo "APP_ROOT_DIR: ${APP_ROOT_DIR:-未設定} (fallback APP_BASE_DIR=${APP_BASE_DIR:-未設定})"
echo "🚀 [2/2] Starting FastAPI..."
if [[ "${DEV_RELOAD:-0}" == "1" ]]; then
  exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
  exec uvicorn app.main:app --host 0.0.0.0 --port 8000
fi