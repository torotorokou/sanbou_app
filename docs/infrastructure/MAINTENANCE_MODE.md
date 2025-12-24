# メンテナンスモード運用ガイド

## 概要

本ドキュメントは、システムメンテナンス時に使用するCloud Runベースのメンテナンスページの運用手順を説明します。

### アーキテクチャ

```
[ユーザー]
    ↓
[GCP Load Balancer + IAP]
    ↓
  ┌─────────────────────┐
  │  URL Map (切替)     │
  └─────────────────────┘
    ↓                ↓
[Cloud Run]    [VM (Docker Compose)]
メンテナンス        本番アプリ
HTTP 503
```

### 特徴

- **最小コスト**: min-instances=0、使用時のみ課金
- **高速切替**: LB設定変更のみ（数秒〜数分）
- **IAP対応**: 認証済みユーザーのみアクセス可能
- **503レスポンス**: Retry-After ヘッダ付き

---

## 前提条件

### デプロイ済み環境

- ✅ Cloud Run サービス: `maintenance-page`
- ✅ プロジェクト: `honest-sanbou-app-prod`
- ✅ リージョン: `asia-northeast1`
- ✅ IAP Service Agent 設定完了

### 必要な権限

- `roles/compute.loadBalancerAdmin` - LB設定変更
- `roles/run.admin` - Cloud Run管理（再デプロイ時）

---

## クイックスタート

### メンテナンスモード有効化（3ステップ）

```bash
# 1. LB設定のバックアップ
gcloud compute url-maps export sanbou-app-url-map \
  --global \
  --project=honest-sanbou-app-prod \
  > /tmp/url-map-backup-$(date +%Y%m%d-%H%M%S).yaml

# 2. メンテナンスバックエンドに切替
gcloud compute url-maps set-default-service sanbou-app-url-map \
  --default-service maintenance-page-backend \
  --global \
  --project=honest-sanbou-app-prod

# 3. 確認
curl -I https://sanbou-app.jp/
# → HTTP/2 503 (メンテナンスページ)
```

### メンテナンスモード解除（2ステップ）

```bash
# 1. 元のバックエンドに戻す
gcloud compute url-maps set-default-service sanbou-app-url-map \
  --default-service sanbou-app-backend-service \
  --global \
  --project=honest-sanbou-app-prod

# 2. 確認
curl -I https://sanbou-app.jp/health
# → HTTP/2 200 (本番アプリ復帰)
```

---

## 詳細手順

### 事前準備（初回のみ）

#### 1. Serverless NEG の作成

```bash
gcloud compute network-endpoint-groups create maintenance-page-neg \
  --region=asia-northeast1 \
  --network-endpoint-type=serverless \
  --cloud-run-service=maintenance-page \
  --project=honest-sanbou-app-prod
```

#### 2. バックエンドサービスの作成

```bash
gcloud compute backend-services create maintenance-page-backend \
  --global \
  --project=honest-sanbou-app-prod \
  --enable-cdn \
  --cache-mode=CACHE_ALL_STATIC
```

#### 3. NEGをバックエンドに追加

```bash
gcloud compute backend-services add-backend maintenance-page-backend \
  --global \
  --network-endpoint-group=maintenance-page-neg \
  --network-endpoint-group-region=asia-northeast1 \
  --project=honest-sanbou-app-prod
```

#### 4. IAP設定の確認

```bash
# IAP Service Agent に invoker 権限が付与されているか確認
gcloud run services get-iam-policy maintenance-page \
  --region=asia-northeast1 \
  --project=honest-sanbou-app-prod
```

---

## 運用フロー

### 計画メンテナンス（推奨）

#### Phase 1: 事前準備（メンテナンス1日前）

```bash
# 1. ユーザーへの事前通知
#    - メール/Slack/アプリ内通知でメンテナンス予定を通知

# 2. バックアップ取得
cd /home/koujiro/work_env/22.Work_React/sanbou_app
make backup ENV=vm_prod

# 3. メンテナンスページの動作確認
cd ops/maintenance
make test PROJECT_ID=honest-sanbou-app-prod

# 4. LB設定のバックアップ
gcloud compute url-maps export sanbou-app-url-map \
  --global \
  --project=honest-sanbou-app-prod \
  > /tmp/url-map-backup-$(date +%Y%m%d-%H%M%S).yaml
```

#### Phase 2: メンテナンス開始

```bash
# 1. 現在時刻を記録
date
# 2025-12-24 13:00:00 JST

# 2. LBをメンテナンスモードに切替
gcloud compute url-maps set-default-service sanbou-app-url-map \
  --default-service maintenance-page-backend \
  --global \
  --project=honest-sanbou-app-prod

# 3. 切替完了確認（数秒〜数分）
for i in {1..5}; do
  echo "=== Attempt $i ==="
  curl -I https://sanbou-app.jp/ 2>&1 | grep "HTTP\|retry-after"
  sleep 5
done
# → HTTP/2 503
# → retry-after: 3600

# 4. 本番アプリの停止（オプション）
# VM上で:
# make down ENV=vm_prod
```

#### Phase 3: メンテナンス作業

```bash
# 例: DBマイグレーション
make al-up-env ENV=vm_prod

# 例: アプリケーション更新
make pull ENV=vm_prod
make up ENV=vm_prod PULL=1
```

#### Phase 4: 動作確認

```bash
# 1. ヘルスチェック
curl -I http://localhost/health
# → HTTP/1.1 200 OK

# 2. 主要エンドポイント確認
curl http://localhost/api/health
# → {"status": "ok"}

# 3. フロントエンド確認
curl -I http://localhost/
# → HTTP/1.1 200 OK
```

#### Phase 5: メンテナンス終了

```bash
# 1. LBを本番モードに戻す
gcloud compute url-maps set-default-service sanbou-app-url-map \
  --default-service sanbou-app-backend-service \
  --global \
  --project=honest-sanbou-app-prod

# 2. 復帰確認
for i in {1..5}; do
  echo "=== Attempt $i ==="
  curl -I https://sanbou-app.jp/health 2>&1 | grep "HTTP"
  sleep 5
done
# → HTTP/2 200

# 3. 完了時刻を記録
date
# 2025-12-24 15:30:00 JST

# 4. ユーザーへの完了通知
```

---

### 緊急メンテナンス（障害発生時）

#### 即座の対応（5分以内）

```bash
# 1. 迅速にLB切替（説明省略）
gcloud compute url-maps set-default-service sanbou-app-url-map \
  --default-service maintenance-page-backend \
  --global \
  --project=honest-sanbou-app-prod

# 2. 確認
curl -I https://sanbou-app.jp/ | grep HTTP
# → HTTP/2 503

# 3. 障害調査開始
```

---

## メンテナンスページの更新

### コード修正後の再デプロイ

```bash
# 1. コード修正
cd ops/maintenance/cloudrun
vim main.py  # または他のエディタ

# 2. ローカルビルド
docker build --platform linux/amd64 \
  -t asia-northeast1-docker.pkg.dev/honest-sanbou-app-prod/sanbou-app/maintenance-page:$(date +%Y%m%d-%H%M%S) \
  -t asia-northeast1-docker.pkg.dev/honest-sanbou-app-prod/sanbou-app/maintenance-page:latest \
  .

# 3. Artifact Registry へプッシュ
docker push asia-northeast1-docker.pkg.dev/honest-sanbou-app-prod/sanbou-app/maintenance-page:latest

# 4. Cloud Run へデプロイ
gcloud run deploy maintenance-page \
  --image asia-northeast1-docker.pkg.dev/honest-sanbou-app-prod/sanbou-app/maintenance-page:latest \
  --region asia-northeast1 \
  --project honest-sanbou-app-prod \
  --no-allow-unauthenticated \
  --min-instances 0 \
  --max-instances 10 \
  --cpu 1 \
  --memory 256Mi \
  --timeout 10s \
  --concurrency 80 \
  --ingress internal-and-cloud-load-balancing

# 5. 動作確認
cd ../
make test PROJECT_ID=honest-sanbou-app-prod
```

---

## トラブルシューティング

### 問題: LB切替後も本番アプリが表示される

**原因**: CDNキャッシュまたはブラウザキャッシュ

**対処法**:
```bash
# 1. CDNキャッシュをクリア（GCP Console から）
#    - ネットワークサービス → Cloud CDN
#    - キャッシュの無効化

# 2. ブラウザで強制リロード
#    - Chrome/Firefox: Ctrl+Shift+R
#    - Safari: Command+Shift+R

# 3. URL Map の確認
gcloud compute url-maps describe sanbou-app-url-map \
  --global \
  --project=honest-sanbou-app-prod \
  --format="get(defaultService)"
```

### 問題: 503が返らない（404や502が返る）

**原因**: Cloud Runサービスの問題

**対処法**:
```bash
# 1. サービス状態確認
cd ops/maintenance
make check PROJECT_ID=honest-sanbou-app-prod

# 2. ログ確認
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=maintenance-page" \
  --project=honest-sanbou-app-prod \
  --limit 20 \
  --format="table(timestamp,severity,textPayload)"

# 3. リビジョンの再デプロイ
make deploy PROJECT_ID=honest-sanbou-app-prod
```

### 問題: IAP認証エラー

**原因**: IAP Service Agent の権限不足

**対処法**:
```bash
# IAP設定の再実行
cd ops/maintenance
make setup-iap PROJECT_ID=honest-sanbou-app-prod
```

### 問題: Cloud Runが起動しない

**原因**: Dockerイメージの問題またはリソース不足

**対処法**:
```bash
# 1. ローカルでテスト
cd ops/maintenance/cloudrun
docker build -t maintenance-test .
docker run -p 8080:8080 -e PORT=8080 maintenance-test
# → http://localhost:8080/ にアクセスして503確認

# 2. メモリ・CPUを増やして再デプロイ
gcloud run deploy maintenance-page \
  --cpu 2 \
  --memory 512Mi \
  ...（その他のオプション）
```

---

## モニタリング

### Cloud Runメトリクス

```bash
# リクエスト数
gcloud monitoring time-series list \
  --filter='resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_count"' \
  --project=honest-sanbou-app-prod

# レスポンスタイム
gcloud monitoring time-series list \
  --filter='resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_latencies"' \
  --project=honest-sanbou-app-prod
```

### ログ確認

```bash
# エラーログ
gcloud logging read "resource.type=cloud_run_revision \
  AND resource.labels.service_name=maintenance-page \
  AND severity>=ERROR" \
  --project=honest-sanbou-app-prod \
  --limit 50

# アクセスログ
gcloud logging read "resource.type=cloud_run_revision \
  AND resource.labels.service_name=maintenance-page \
  AND httpRequest.status=503" \
  --project=honest-sanbou-app-prod \
  --limit 20
```

---

## コスト管理

### 現在の設定

- **min-instances**: 0（アイドル時は課金なし）
- **max-instances**: 10
- **CPU**: 1
- **Memory**: 256Mi
- **Timeout**: 10s
- **Concurrency**: 80

### 月間コスト試算

**想定**: 月間メンテナンス3回、各2時間、アクセス1000req/h

- リクエスト課金: 6000リクエスト × $0.40/100万 ≈ $0.002
- インスタンス時間: 6時間 × 256MiB × $0.00001563/MiB-秒 ≈ $0.14
- **合計**: 約 $0.15/月

### コスト削減のヒント

1. **min-instances=0を維持**: アイドル時の課金を避ける
2. **短いタイムアウト**: 不要なインスタンス時間を削減
3. **低い同時実行数**: インスタンス数を抑制
4. **CDN活用**: 静的コンテンツのキャッシュ

---

## チェックリスト

### メンテナンス開始前

- [ ] ユーザーへの事前通知（1日前）
- [ ] DBバックアップ取得
- [ ] メンテナンスページの動作確認
- [ ] LB設定のバックアップ
- [ ] 作業手順の確認
- [ ] ロールバック手順の確認

### メンテナンス中

- [ ] LB切替完了確認
- [ ] メンテナンスページ表示確認
- [ ] 作業進捗の記録
- [ ] 問題発生時の対応記録

### メンテナンス終了後

- [ ] 動作確認（ヘルスチェック）
- [ ] LB切替（本番復帰）
- [ ] 本番アプリ表示確認
- [ ] ユーザーへの完了通知
- [ ] 作業完了報告
- [ ] 問題点の記録と改善提案

---

## 関連ドキュメント

- [ops/maintenance/cloudrun/README.md](../../ops/maintenance/cloudrun/README.md) - 技術詳細
- [ops/maintenance/Makefile](../../ops/maintenance/Makefile) - 運用コマンド
- [docs/infrastructure/MAKEFILE_GUIDE.md](./MAKEFILE_GUIDE.md) - Makefile全体ガイド

---

## 改訂履歴

- 2025-12-24: 初版作成
