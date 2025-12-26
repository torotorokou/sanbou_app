# GCP Application Default Credentials (ADC) セットアップガイド

**作成日**: 2025年12月3日  
**対象**: sanbou_app 開発者・運用担当者

---

## 目次

1. [概要](#概要)
2. [ADCとは](#adcとは)
3. [ローカル開発環境でのセットアップ](#ローカル開発環境でのセットアップ)
4. [GCE (stg/prod) 環境でのセットアップ](#gce-stgprod-環境でのセットアップ)
5. [トラブルシューティング](#トラブルシューティング)
6. [移行前後の比較](#移行前後の比較)
7. [将来の Workload Identity 対応](#将来の-workload-identity-対応)

---

## 概要

このプロジェクトでは、GCP サービスアカウントの **JSON キーファイル依存を廃止**し、**Application Default Credentials (ADC)** に完全移行しました。

### 変更の目的

1. **セキュリティ向上**: JSON キーファイルの漏洩リスクを排除
2. **運用簡素化**: キーファイルのマウント・環境変数設定が不要
3. **将来対応**: Workload Identity 等への移行が容易

### 影響範囲

- **Python コード**: `storage.Client()` 等の引数なしコンストラクタを使用
- **環境変数**: `GOOGLE_APPLICATION_CREDENTIALS` を削除
- **Docker Compose**: `secrets/` マウントを削除
- **スクリプト**: `startup.sh`, `download_master_data.py` を ADC 対応に変更

---

## ADCとは

**Application Default Credentials (ADC)** は、GCP クライアントライブラリが自動的に認証情報を検出・利用する仕組みです。

### 認証情報の検出順序

1. **環境変数 `GOOGLE_APPLICATION_CREDENTIALS`** (設定されている場合)
2. **gcloud CLI の認証情報** (`gcloud auth application-default login`)
3. **GCE / GKE のメタデータサーバー** (VM / Pod にアタッチされたサービスアカウント)

**本プロジェクトでは**:

- ローカル開発: `gcloud auth application-default login` を使用 (2番目)
- GCE (stg/prod): VM にアタッチされたサービスアカウント (3番目)
- 環境変数 `GOOGLE_APPLICATION_CREDENTIALS` は**使用しない** (1番目をスキップ)

---

## ローカル開発環境でのセットアップ

### 前提条件

- gcloud CLI がインストールされている
- GCP プロジェクトへのアクセス権限がある

### 初回セットアップ手順

#### 1. gcloud CLI のインストール (未インストールの場合)

```bash
# macOS (Homebrew)
brew install google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Windows
# https://cloud.google.com/sdk/docs/install からインストーラーをダウンロード
```

#### 2. gcloud CLI の初期化

```bash
gcloud init
```

- GCP プロジェクトを選択 (`sanbouapp-dev` / `sanbouapp-stg` / `sanbouapp-prod`)
- デフォルトリージョンを設定 (例: `asia-northeast1`)

#### 3. ADC の設定

```bash
gcloud auth application-default login
```

- ブラウザが開き、Google アカウントでログイン
- 認証情報が `~/.config/gcloud/application_default_credentials.json` に保存される
- **この JSON ファイルは自動生成され、Git にコミットする必要はありません**

#### 4. 認証確認

```bash
# 現在の認証情報を確認
gcloud auth list

# ADC が設定されているか確認
gcloud auth application-default print-access-token
```

#### 5. Docker Compose 起動

```bash
cd /path/to/sanbou_app
make up ENV=local_dev
```

- コンテナ内から ADC を使用して GCS にアクセスします
- `GOOGLE_APPLICATION_CREDENTIALS` 環境変数は**不要**です

### よくある質問

**Q: コンテナ内から ~/.config/gcloud/ にアクセスできますか？**

A: できます。`docker-compose.dev.yml` では、ホストの `~/.config/gcloud/` をマウントする必要は**ありません**。gcloud CLI がコンテナ内で ADC を検出します。

**Q: JSON キーファイルは完全に不要ですか？**

A: はい。`secrets/dev_key.json` は使用されません。削除しても問題ありません。

**Q: GCS へのアクセス権限が不足している場合は？**

A: IAM でユーザーアカウントに以下のロールを付与してください:

- `roles/storage.objectViewer` (読み取り)
- `roles/storage.objectAdmin` (読み書き)

---

## GCE (stg/prod) 環境でのセットアップ

### 前提条件

- GCE VM が作成済み
- サービスアカウントが作成済み

### 1. サービスアカウントの作成

```bash
# stg 環境用サービスアカウント作成
gcloud iam service-accounts create sanbou-stg-sa \
  --display-name="Sanbou STG Service Account" \
  --project=sanbouapp-stg

# prod 環境用サービスアカウント作成
gcloud iam service-accounts create sanbou-prod-sa \
  --display-name="Sanbou PROD Service Account" \
  --project=sanbouapp-prod
```

### 2. 必要な権限を付与

```bash
# stg 環境
export PROJECT_ID=sanbouapp-stg
export SA_EMAIL=sanbou-stg-sa@${PROJECT_ID}.iam.gserviceaccount.com

# GCS 読み取り権限
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.objectViewer"

# BigQuery 読み取り権限 (必要に応じて)
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/bigquery.dataViewer"

# Secret Manager アクセス (必要に応じて)
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/secretmanager.secretAccessor"
```

同様に prod 環境でも実行してください。

### 3. VM にサービスアカウントをアタッチ

#### 新規 VM 作成時

```bash
gcloud compute instances create sanbou-stg-vm \
  --project=sanbouapp-stg \
  --zone=asia-northeast1-a \
  --machine-type=e2-standard-4 \
  --service-account=${SA_EMAIL} \
  --scopes=https://www.googleapis.com/auth/cloud-platform
```

#### 既存 VM の場合

```bash
# VM を停止
gcloud compute instances stop sanbou-stg-vm --zone=asia-northeast1-a

# サービスアカウントをアタッチ
gcloud compute instances set-service-account sanbou-stg-vm \
  --zone=asia-northeast1-a \
  --service-account=${SA_EMAIL} \
  --scopes=https://www.googleapis.com/auth/cloud-platform

# VM を起動
gcloud compute instances start sanbou-stg-vm --zone=asia-northeast1-a
```

### 4. VM 内での確認

```bash
# VM に SSH 接続
gcloud compute ssh sanbou-stg-vm --zone=asia-northeast1-a

# サービスアカウントの確認
curl -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email

# ADC のアクセストークン取得確認
curl -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token
```

### 5. Docker Compose 起動

```bash
cd /path/to/sanbou_app

# stg 環境
COMPOSE_PROFILES=edge make up ENV=vm_stg

# prod 環境
COMPOSE_PROFILES=edge make up ENV=vm_prod
```

- コンテナ内から **VM のメタデータサーバー経由で ADC を使用**します
- `GOOGLE_APPLICATION_CREDENTIALS` 環境変数は**不要**です
- `secrets/stg_key.json` や `secrets/prod_key.json` は**不要**です

---

## トラブルシューティング

### ローカル開発環境

#### エラー: `DefaultCredentialsError: Could not automatically determine credentials`

**原因**: ADC が設定されていない

**解決策**:

```bash
gcloud auth application-default login
```

#### エラー: `403 Forbidden` (GCS アクセス時)

**原因**: ユーザーアカウントに権限がない

**解決策**:

```bash
# 自分のアカウントを確認
gcloud auth list

# IAM で権限を付与 (プロジェクトオーナーに依頼)
gcloud projects add-iam-policy-binding sanbouapp-dev \
  --member="user:YOUR_EMAIL@example.com" \
  --role="roles/storage.objectViewer"
```

### GCE 環境

#### エラー: `DefaultCredentialsError: Could not automatically determine credentials`

**原因**: VM にサービスアカウントがアタッチされていない

**解決策**:

```bash
# VM のサービスアカウントを確認
gcloud compute instances describe sanbou-stg-vm --zone=asia-northeast1-a \
  --format="value(serviceAccounts[0].email)"

# 何も表示されない場合は、サービスアカウントをアタッチ (上記手順参照)
```

#### エラー: `403 Forbidden` (GCS アクセス時)

**原因**: サービスアカウントに権限がない

**解決策**:

```bash
# サービスアカウントの権限を確認
gcloud projects get-iam-policy sanbouapp-stg \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:sanbou-stg-sa@*"

# 権限を付与
gcloud projects add-iam-policy-binding sanbouapp-stg \
  --member="serviceAccount:sanbou-stg-sa@sanbouapp-stg.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"
```

#### コンテナ内から ADC が機能しない

**原因**: Docker ネットワークがメタデータサーバーへのアクセスをブロックしている

**解決策**:

```bash
# コンテナ内で確認
docker exec -it <container_id> bash
curl -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token

# アクセスできない場合は、Docker ネットワーク設定を確認
# (通常は問題ありません)
```

---

## 移行前後の比較

### 移行前 (JSON キー使用)

**Python コード**:

```python
from google.cloud import storage

def get_gcs_client():
    credentials_path = "/backend/secrets/dev_key.json"
    return storage.Client.from_service_account_json(credentials_path)
```

**docker-compose.yml**:

```yaml
volumes:
  - ../secrets:/backend/secrets:ro
environment:
  GOOGLE_APPLICATION_CREDENTIALS: /backend/secrets/dev_key.json
```

**環境変数 (.env)**:

```bash
GOOGLE_APPLICATION_CREDENTIALS=/backend/secrets/dev_key.json
```

### 移行後 (ADC 使用)

**Python コード**:

```python
from google.cloud import storage

def get_gcs_client():
    # ADC を使用 (引数なし)
    return storage.Client()
```

**docker-compose.yml**:

```yaml
# secrets/ マウント不要
# GOOGLE_APPLICATION_CREDENTIALS 環境変数不要
```

**環境変数 (.env)**:

```bash
# === GCP 認証 (ADC) ===
# Application Default Credentials を使用
# ローカル: gcloud auth application-default login を実行
# GCE: VM にサービスアカウントをアタッチ
# GOOGLE_APPLICATION_CREDENTIALS 環境変数は不要です
```

---

## 将来の Workload Identity 対応

ADC を使用することで、将来的に **Workload Identity** (GKE) や **Workload Identity Federation** (Cloud Run) への移行が容易になります。

### Workload Identity (GKE) への移行

1. **GKE クラスタで Workload Identity を有効化**:

```bash
gcloud container clusters update CLUSTER_NAME \
  --workload-pool=PROJECT_ID.svc.id.goog
```

2. **Kubernetes ServiceAccount を作成**:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: sanbou-ksa
  namespace: default
  annotations:
    iam.gke.io/gcp-service-account: sanbou-stg-sa@PROJECT_ID.iam.gserviceaccount.com
```

3. **IAM バインディング**:

```bash
gcloud iam service-accounts add-iam-policy-binding \
  sanbou-stg-sa@PROJECT_ID.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:PROJECT_ID.svc.id.goog[default/sanbou-ksa]"
```

4. **アプリケーションコードは変更不要**:
   - `storage.Client()` 等の ADC 前提コードがそのまま動作します
   - Pod 内から自動的に Workload Identity が使用されます

### Cloud Run への移行

1. **Cloud Run サービスにサービスアカウントを指定**:

```bash
gcloud run deploy sanbou-api \
  --image gcr.io/PROJECT_ID/sanbou-api:latest \
  --service-account=sanbou-stg-sa@PROJECT_ID.iam.gserviceaccount.com
```

2. **アプリケーションコードは変更不要**:
   - ADC が自動的に Cloud Run のサービスアカウントを使用します

---

## 関連ドキュメント

- [GCP Application Default Credentials 公式ドキュメント](https://cloud.google.com/docs/authentication/application-default-credentials)
- [gcloud auth application-default login](https://cloud.google.com/sdk/gcloud/reference/auth/application-default/login)
- [Workload Identity (GKE)](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity)
- [セキュリティ監査レポート](./20251203_SECURITY_AUDIT_REPORT.md)
- [IAP 認証実装ガイド](./20251203_IAP_AUTHENTICATION_IMPLEMENTATION.md)

---

## まとめ

このドキュメントに従って ADC をセットアップすることで、以下が実現されます:

✅ **JSON キーファイル不要**  
✅ **セキュリティ向上**  
✅ **ローカル / GCE / GKE / Cloud Run で統一的な認証方式**  
✅ **将来の Workload Identity 対応が容易**

質問がある場合は、開発チームに連絡してください。
