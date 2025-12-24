# メンテナンス運用クイックリファレンス

## 🚨 緊急時（即座に実行）

```bash
# メンテナンスモードON（30秒）
gcloud compute url-maps set-default-service sanbou-app-url-map \
  --default-service maintenance-page-backend \
  --global --project=honest-sanbou-app-prod

# 確認
curl -I https://sanbou-app.jp/ | grep HTTP
```

## ✅ 計画メンテナンス（標準フロー）

### 1. 事前準備（前日）

```bash
# バックアップ
make backup ENV=vm_prod

# メンテナンスページ確認
cd ops/maintenance && make test PROJECT_ID=honest-sanbou-app-prod

# LB設定バックアップ
gcloud compute url-maps export sanbou-app-url-map \
  --global --project=honest-sanbou-app-prod \
  > /tmp/url-map-backup-$(date +%Y%m%d).yaml
```

### 2. メンテナンス開始

```bash
# LB切替
gcloud compute url-maps set-default-service sanbou-app-url-map \
  --default-service maintenance-page-backend \
  --global --project=honest-sanbou-app-prod

# 確認（503が返るまで待つ）
watch -n 5 "curl -I https://sanbou-app.jp/ | grep HTTP"
```

### 3. 作業実施

```bash
# 例: マイグレーション
make al-up-env ENV=vm_prod

# 例: アプリ更新
make up ENV=vm_prod PULL=1
```

### 4. 動作確認

```bash
# VM内でヘルスチェック
curl -I http://localhost/health
```

### 5. メンテナンス終了

```bash
# LB復帰
gcloud compute url-maps set-default-service sanbou-app-url-map \
  --default-service sanbou-app-backend-service \
  --global --project=honest-sanbou-app-prod

# 確認（200が返るまで待つ）
watch -n 5 "curl -I https://sanbou-app.jp/health | grep HTTP"
```

## 🔧 よく使うコマンド

### メンテナンスページ管理

```bash
cd ops/maintenance

# デプロイ
make deploy PROJECT_ID=honest-sanbou-app-prod

# テスト
make test PROJECT_ID=honest-sanbou-app-prod

# ステータス確認
make check PROJECT_ID=honest-sanbou-app-prod

# ヘルプ
make help
```

### LB状態確認

```bash
# 現在のデフォルトバックエンド
gcloud compute url-maps describe sanbou-app-url-map \
  --global --project=honest-sanbou-app-prod \
  --format="get(defaultService)"

# バックエンド一覧
gcloud compute backend-services list \
  --global --project=honest-sanbou-app-prod
```

### Cloud Run確認

```bash
# サービス状態
gcloud run services describe maintenance-page \
  --region=asia-northeast1 \
  --project=honest-sanbou-app-prod

# ログ確認（最新20件）
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=maintenance-page" \
  --project=honest-sanbou-app-prod \
  --limit 20 \
  --format="table(timestamp,severity,textPayload)"
```

## 🐛 トラブルシューティング

### 問題: LB切替後も本番が表示される

```bash
# CDNキャッシュクリア（GCP Console）
# → ネットワークサービス → Cloud CDN → キャッシュの無効化

# URL Map確認
gcloud compute url-maps describe sanbou-app-url-map \
  --global --project=honest-sanbou-app-prod
```

### 問題: 503以外のエラー

```bash
# Cloud Runログ確認
gcloud logging read \
  "resource.type=cloud_run_revision AND severity>=ERROR" \
  --project=honest-sanbou-app-prod --limit 10

# 再デプロイ
cd ops/maintenance && make deploy PROJECT_ID=honest-sanbou-app-prod
```

## 📝 チェックリスト

### 開始前
- [ ] ユーザー通知（1日前）
- [ ] DBバックアップ
- [ ] LB設定バックアップ
- [ ] メンテナンスページ動作確認

### 終了後
- [ ] 動作確認
- [ ] LB復帰確認
- [ ] ユーザー通知
- [ ] 作業記録

## 📚 詳細ドキュメント

[docs/infrastructure/MAINTENANCE_MODE.md](./MAINTENANCE_MODE.md)
