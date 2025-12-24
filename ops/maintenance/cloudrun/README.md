# メンテナンスページ Cloud Run サービス

## 概要

本番システムのメンテナンス時に HTTP 503 を返すための軽量 Cloud Run サービスです。

### 特徴

- **最小構成**: FastAPI + uvicorn で実装した軽量アプリ
- **コスト最適化**: min-instances=0、最小CPU/メモリ、短いタイムアウト
- **セキュリティ**: IAP + LB 経由でアクセス（allUsers 公開なし）
- **シンプル**: 外部リソース依存なし、HTML 1ページのみ

### アーキテクチャ

```
[ユーザー] → [GCP LB + IAP] → [Cloud Run (maintenance)] → HTTP 503
                              ↓（通常時）
                              [VM + Docker Compose (本番アプリ)]
```

メンテナンス時は LB のバックエンドを Cloud Run に切り替えることで、本番アプリを停止せずにメンテナンス表示が可能です。

---

## 前提条件

### 必要な環境

- Google Cloud SDK (`gcloud` コマンド)
- Docker（ローカルテスト用、オプション）
- GCP プロジェクトとリージョン設定済み

### 権限

以下の IAM ロールが必要です：

- `roles/run.admin` - Cloud Run サービスの作成・更新
- `roles/iam.serviceAccountUser` - サービスアカウントの使用
- `roles/storage.admin` または `roles/artifactregistry.writer` - イメージの push（Cloud Build 使用時は不要）

### 重要：初回デプロイ前の準備

**初めて Cloud Run にデプロイする場合、Cloud Build のサービスアカウントに権限を付与する必要があります。**

```bash
# Makefile を使う場合（推奨）
make setup-maintenance-cloudbuild-permissions PROJECT_ID=honest-sanbou-app-prod

# または手動で設定する場合（下記の「Cloud Build 権限設定」セクションを参照）
```

---

## デプロイ手順

### 0. Cloud Build 権限設定（初回のみ）

**最初のデプロイ前に必ず実行してください。**

#### 方法A: メンテナンス専用 Makefile を使用（推奨）

```bash
# ops/maintenance/ ディレクトリに移動
cd ops/maintenance

# 権限設定
make setup-cloudbuild-permissions PROJECT_ID=honest-sanbou-app-prod

# または、ルートディレクトリから
make maintenance-setup-cloudbuild PROJECT_ID=honest-sanbou-app-prod
```

#### 方法B: 手動設定

```bash
# プロジェクト番号を取得
export PROJECT_ID="honest-sanbou-app-prod"
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

echo "Project Number: $PROJECT_NUMBER"

# Compute Engine デフォルトサービスアカウントに Storage Admin を付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/storage.admin"

# Cloud Build サービスアカウントに Cloud Run Admin を付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"

# Cloud Build サービスアカウントに Service Account User を付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

**注意**: 権限の反映には数分かかる場合があります。

### 1. 環境変数の設定

```bash
# プロジェクトとリージョン
export PROJECT_ID="honest-sanbou-app-prod"  # または stg
export REGION="asia-northeast1"
export SERVICE_NAME="maintenance-page"

# gcloud 設定
gcloud config set project $PROJECT_ID
gcloud config set run/region $REGION
```

### 2. Cloud Run へのデプロイ

#### 方法A: メンテナンス専用 Makefile を使用（推奨）

```bash
# ops/maintenance/ ディレクトリに移動
cd ops/maintenance

# 初回デプロイ前に権限設定（一度だけ実行）
make setup-cloudbuild-permissions PROJECT_ID=honest-sanbou-app-prod

# デプロイ実行
make deploy PROJECT_ID=honest-sanbou-app-prod

# または、ルートディレクトリから
make maintenance-deploy PROJECT_ID=honest-sanbou-app-prod
```

**利用可能なコマンド**:
```bash
cd ops/maintenance

make deploy PROJECT_ID=xxx              # Cloud Run にデプロイ
make test PROJECT_ID=xxx                # 動作確認
make check PROJECT_ID=xxx               # サービス状態確認
make setup-iap PROJECT_ID=xxx           # IAP Service Agent 設定
make setup-cloudbuild-permissions PROJECT_ID=xxx  # Cloud Build 権限設定
make clean PROJECT_ID=xxx               # サービス削除
make help                                # ヘルプ表示
```

#### 方法B: Cloud Build を直接使用

```bash
cd ops/maintenance/cloudrun

gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --no-allow-unauthenticated \
  --min-instances 0 \
  --max-instances 10 \
  --cpu 1 \
  --memory 256Mi \
  --timeout 10s \
  --concurrency 80 \
  --ingress internal-and-cloud-load-balancing \
  --service-account maintenance-page@${PROJECT_ID}.iam.gserviceaccount.com
```

**注意**: 
- `--no-allow-unauthenticated` を必ず指定（公開アクセス禁止）
- `--ingress internal-and-cloud-load-balancing` で LB 経由のみ許可
- 初回デプロイ時は API 有効化と Artifact Registry 作成の確認が表示されます（Y で承認）

#### 方法C: ローカルビルド + Artifact Registry

```bash
cd ops/maintenance/cloudrun

# イメージビルド
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/sanbou-app/maintenance-page:latest .

# Artifact Registry への push（認証設定済みの場合）
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/sanbou-app/maintenance-page:latest

# Cloud Run にデプロイ
gcloud run deploy $SERVICE_NAME \
  --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/sanbou-app/maintenance-page:latest \
  --platform managed \
  --region $REGION \
  --no-allow-unauthenticated \
  --min-instances 0 \
  --max-instances 10 \
  --cpu 1 \
  --memory 256Mi \
  --timeout 10s \
  --concurrency 80 \
  --ingress internal-and-cloud-load-balancing \
  --service-account maintenance-page@${PROJECT_ID}.iam.gserviceaccount.com
```

**注意**: サービスアカウントは任意です。指定しない場合はデフォルトの Compute Engine サービスアカウントが使用されます。

### 3. デプロイの確認

---

## IAP 経由でのアクセス設定

Cloud Run を IAP + LB 経由でアクセスさせるには、IAP の Service Agent に `roles/run.invoker` を付与する必要があります。

### 1. IAP Service Identity の作成

```bash
gcloud beta services identity create --service=iap.googleapis.com --project=$PROJECT_ID
```

出力例:
```
Service identity created: service-123456789@gcp-sa-iap.iam.gserviceaccount.com
```

### 2. Project Number の取得

```bash
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
echo "Project Number: $PROJECT_NUMBER"
```

### 3. IAP Service Agent に Invoker 権限を付与

```bash
gcloud run services add-iam-policy-binding $SERVICE_NAME \
  --region=$REGION \
  --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-iap.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

---

## 動作確認

### Cloud Run サービスの URL 確認

```bash
gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)"
```

### ローカルからの認証付きテスト

```bash
# Identity Token を取得
TOKEN=$(gcloud auth print-identity-token)

# Cloud Run にリクエスト（503 が返る）
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

curl -i -H "Authorization: Bearer $TOKEN" $SERVICE_URL
```

期待される結果:
```
HTTP/2 503
retry-after: 3600
cache-control: no-store, no-cache, must-revalidate, max-age=0
...

<!DOCTYPE html>
<html lang="ja">
...
```

### IAP + LB 経由での確認（本番環境）

LB 設定後、実際のドメインからアクセス:

```bash
curl -i https://sanbou-app.jp/
```

IAP 認証が通れば、メンテナンスページ（503）が返されます。

---

## LB バックエンドの切り替え（メンテナンスモード ON/OFF）

### 前提: Serverless NEG の作成

Cloud Run サービス用の Serverless Network Endpoint Group (NEG) を作成します。

```bash
# Serverless NEG 作成
gcloud compute network-endpoint-groups create maintenance-page-neg \
  --region=$REGION \
  --network-endpoint-type=serverless \
  --cloud-run-service=$SERVICE_NAME
```

### バックエンドサービスへの追加

```bash
# 既存の LB バックエンドサービス名を確認
gcloud compute backend-services list

# Serverless NEG をバックエンドサービスに追加
export BACKEND_SERVICE_NAME="sanbou-app-backend-service"  # 実際の名前に置き換え

gcloud compute backend-services add-backend $BACKEND_SERVICE_NAME \
  --global \
  --network-endpoint-group=maintenance-page-neg \
  --network-endpoint-group-region=$REGION
```

### メンテナンスモードの切り替え

#### メンテナンスモード ON（Cloud Run にルーティング）

```bash
# URL Map を更新してデフォルトバックエンドを Cloud Run に変更
gcloud compute url-maps edit sanbou-app-url-map  # 実際の名前に置き換え
```

YAML エディタで `defaultService` を変更:

```yaml
defaultService: https://www.googleapis.com/compute/v1/projects/<PROJECT_ID>/global/backendServices/<MAINTENANCE_BACKEND_SERVICE>
```

**または CLI で直接変更**:

```bash
export MAINTENANCE_BACKEND_SERVICE="maintenance-page-backend"

gcloud compute url-maps set-default-service sanbou-app-url-map \
  --default-service $MAINTENANCE_BACKEND_SERVICE \
  --global
```

#### メンテナンスモード OFF（VM にルーティング）

```bash
# 元の VM バックエンドに戻す
export ORIGINAL_BACKEND_SERVICE="sanbou-app-backend-service"

gcloud compute url-maps set-default-service sanbou-app-url-map \
  --default-service $ORIGINAL_BACKEND_SERVICE \
  --global
```

### 反映の確認

変更は数分で反映されます：

```bash
# URL Map の確認
gcloud compute url-maps describe sanbou-app-url-map --global

# 実際のアクセステスト
curl -I https://sanbou-app.jp/
```

---

## コスト最適化のポイント

1. **min-instances=0**: アクセスがない時はインスタンス0
2. **最小リソース**: CPU 1, Memory 256Mi
3. **短いタイムアウト**: 10秒（静的HTML配信のみ）
4. **低い同時実行数**: concurrency 80（デフォルトより低め）
5. **内部トラフィックのみ**: `--ingress internal-and-cloud-load-balancing`

月間コスト試算（アクセスが少ない場合）:
- インスタンス時間: ほぼ $0（min-instances=0）
- リクエスト課金: 月100万リクエストでも数ドル程度

---

## トラブルシューティング

### Cloud Build 権限エラー

エラー例:
```
ERROR: Build failed because the default service account is missing required IAM permissions.
PERMISSION_DENIED: IAM permission denied for service account xxx-compute@developer.gserviceaccount.com
```

**解決方法**:
```bash
# ops/maintenance/ ディレクトリから
cd ops/maintenance
make setup-cloudbuild-permissions PROJECT_ID=honest-sanbou-app-prod

# または、ルートディレクトリから
make maintenance-setup-cloudbuild PROJECT_ID=honest-sanbou-app-prod

# 数分待ってから再デプロイ
make deploy PROJECT_ID=honest-sanbou-app-prod
```

### 503 以外のエラーが返る

- Cloud Run サービスのログを確認:
  ```bash
  gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" \
    --limit 50 --format json
  ```

### IAP 経由でアクセスできない

- IAP Service Agent に `roles/run.invoker` が付与されているか確認:
  ```bash
  gcloud run services get-iam-policy $SERVICE_NAME --region=$REGION
  ```
- LB の Health Check が通っているか確認（GCP Console）

### LB 切り替えが反映されない

- URL Map の変更が正しいか確認:
  ```bash
  gcloud compute url-maps describe sanbou-app-url-map --global
  ```
- CDN キャッシュが有効な場合はパージが必要

---

## セキュリティ上の注意

1. **公開アクセス禁止**: `--no-allow-unauthenticated` を必ず指定
2. **組織ポリシー遵守**: `allUsers` による公開は使用しない
3. **最小権限**: サービスアカウントには必要最小限の権限のみ
4. **内部トラフィック**: `--ingress internal-and-cloud-load-balancing` で LB 経由のみ許可

---

## 運用フロー例

### 計画メンテナンス

1. **事前通知**: ユーザーに対してメンテナンス予定を通知
2. **バックアップ**: DB のバックアップを取得
3. **LB 切替**: URL Map を Cloud Run に変更
4. **メンテナンス実施**: VM 上で作業
5. **動作確認**: テスト環境で確認
6. **LB 復帰**: URL Map を元の VM に戻す
7. **動作確認**: 本番環境でヘルスチェック

### 緊急メンテナンス

1. **即座に LB 切替**: Cloud Run にルーティング
2. **問題調査・修正**: VM 上で対応
3. **LB 復帰**: 修正完了後、元に戻す

---

## 参考リンク

- [Cloud Run ドキュメント](https://cloud.google.com/run/docs)
- [IAP と Cloud Run の統合](https://cloud.google.com/iap/docs/enabling-cloud-run)
- [Load Balancing with Cloud Run](https://cloud.google.com/load-balancing/docs/https/setting-up-https-serverless)
- [FastAPI ドキュメント](https://fastapi.tiangolo.com/)

---

## 更新履歴

- 2025-12-24: 初版作成
