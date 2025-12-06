# 🔐 セキュリティ対応アクションプラン (2025-12-06)

## ✅ 完了済み対応

### 1. Git 管理からの削除 ✓
- [x] env/ と secrets/ の実設定ファイルを Git 管理から削除
- [x] .gitignore を修正してディレクトリレベルで除外
- [x] テンプレートファイル (.example, .template) のみ Git 管理対象
- [x] commit & push 済み (commit: 65053574)

### 2. Pre-commit フックの導入 ✓
- [x] `.git/hooks/pre-commit` を作成
- [x] 機密ファイルパターンの検出
- [x] 機密情報（パスワード、API キー）の検出
- [x] 実行権限付与済み

### 3. Git 履歴削除スクリプトの準備 ✓
- [x] `scripts/cleanup_git_history.sh` を作成
- [x] git-filter-repo を使用した安全な削除手順
- [x] 実行権限付与済み

---

## 🔥 今すぐ実行すべき対応（優先度: 緊急）

### Priority 1: 本番環境の認証情報ローテーション

**リスク**: 本番データベースとシステムへの不正アクセス

#### 1.1 PostgreSQL パスワード変更 🔴

```bash
# 本番 VM に SSH 接続
ssh k_tsuchida@34.180.102.141

# PostgreSQL コンテナに入る
cd ~/work_env/sanbou_app
docker compose -f docker/docker-compose.prod.yml exec db psql -U postgres

# パスワード変更
ALTER USER myuser WITH PASSWORD '新しい強力なパスワード_32文字以上';
\q

# env と secrets ファイルを更新
nano env/.env.vm_prod
# POSTGRES_PASSWORD: 新しいパスワードを設定

nano secrets/.env.vm_prod.secrets
# POSTGRES_PASSWORD: 新しいパスワードを設定

# サービス再起動
docker compose -f docker/docker-compose.prod.yml restart
```

**検証**:
```bash
# 接続テスト
docker compose -f docker/docker-compose.prod.yml exec core_api curl http://localhost:8000/health
```

**所要時間**: 10分  
**影響範囲**: 本番環境の一時停止（数秒）

---

### Priority 2: GCP サービスアカウント鍵の再発行 🔴

**リスク**: GCS バケット、Artifact Registry への不正アクセス

#### 2.1 既存の鍵を確認・無効化

```bash
# 現在の鍵をリスト
gcloud iam service-accounts keys list \
  --iam-account=sanbou-app-sa@honest-sanbou-app-prod.iam.gserviceaccount.com

# 流出した鍵 ID を無効化（KEY_ID は上記コマンドの出力から）
gcloud iam service-accounts keys delete <KEY_ID> \
  --iam-account=sanbou-app-sa@honest-sanbou-app-prod.iam.gserviceaccount.com
```

#### 2.2 新しい鍵を発行

```bash
# 新しい鍵を生成
gcloud iam service-accounts keys create ~/new-gcp-sa-key.json \
  --iam-account=sanbou-app-sa@honest-sanbou-app-prod.iam.gserviceaccount.com

# 本番 VM に転送
scp -i ~/.ssh/gcp_sanbou ~/new-gcp-sa-key.json k_tsuchida@34.180.102.141:~/work_env/sanbou_app/secrets/

# VM 上で配置
ssh k_tsuchida@34.180.102.141
cd ~/work_env/sanbou_app
mv secrets/new-gcp-sa-key.json secrets/gcp-sa-prod.json
chmod 600 secrets/gcp-sa-prod.json

# secrets/.env.vm_prod.secrets を更新
nano secrets/.env.vm_prod.secrets
# GCP_SERVICE_ACCOUNT_KEY_PATH=/backend/secrets/gcp-sa-prod.json

# サービス再起動
docker compose -f docker/docker-compose.prod.yml restart
```

**検証**:
```bash
# GCS アクセステスト
docker compose -f docker/docker-compose.prod.yml exec core_api \
  python -c "from google.cloud import storage; client = storage.Client(); print(list(client.list_buckets()))"
```

**所要時間**: 15分  
**影響範囲**: 本番環境の一時停止（再起動時）

---

### Priority 3: Git 履歴から機密ファイルを完全削除 🔴

**リスク**: 既にクローンした人が履歴から情報を取得可能

#### 3.1 git-filter-repo のインストール

```bash
# Ubuntu/WSL
sudo apt-get update
sudo apt-get install git-filter-repo

# または pip
pip3 install git-filter-repo
```

#### 3.2 スクリプト実行

```bash
cd /home/koujiro/work_env/22.Work_React/sanbou_app

# バックアップ作成
cd ..
tar -czf sanbou_app_backup_$(date +%Y%m%d_%H%M%S).tar.gz sanbou_app/
cd sanbou_app

# スクリプト実行
bash scripts/cleanup_git_history.sh
```

#### 3.3 リモートに強制プッシュ

```bash
# 全ブランチを強制プッシュ
git push origin --force --all

# タグも強制プッシュ
git push origin --force --tags
```

#### 3.4 チームメンバーへの通知

```markdown
【重要】Git リポジトリの履歴を書き換えました

セキュリティ対応のため、機密ファイルを Git 履歴から削除しました。
以下の手順で対応をお願いします:

1. 作業中の変更を退避
   git stash

2. 既存のローカルリポジトリを削除
   cd ~/work_env
   rm -rf 22.Work_React/sanbou_app

3. 新規にクローン
   git clone https://github.com/torotorokou/sanbou_app.git
   cd sanbou_app
   git checkout <あなたのブランチ>

4. 退避した変更を復元（必要に応じて）
   git stash pop
```

**所要時間**: 30分（チーム対応含む）  
**影響範囲**: 全開発者のローカルリポジトリ

---

## ⚠️ 24時間以内に実行すべき対応（優先度: 高）

### Priority 4: リポジトリの可視性確認

```bash
# GitHub リポジトリの設定確認
# https://github.com/torotorokou/sanbou_app/settings

# public の場合 → private に変更
# Settings → Danger Zone → Change repository visibility → Make private
```

**所要時間**: 2分  
**影響範囲**: なし

---

### Priority 5: ステージング環境の認証情報ローテーション

Priority 1 と同じ手順を vm_stg 環境で実施

**所要時間**: 25分  
**影響範囲**: ステージング環境の一時停止

---

### Priority 6: IAP 設定の確認

```bash
# IAP OAuth クライアント ID の確認
gcloud iap oauth-clients list --project=honest-sanbou-app-prod

# 必要に応じて新しいクライアント ID を作成
gcloud iap oauth-clients create \
  --display-name="Sanbou App IAP Client" \
  --project=honest-sanbou-app-prod
```

**所要時間**: 10分  
**影響範囲**: IAP 経由のアクセス（再設定時）

---

## 📅 1週間以内に実行すべき対応（優先度: 中）

### Priority 7: Google Secret Manager への移行

#### 7.1 Secret Manager にシークレットを登録

```bash
# 本番 DB パスワード
echo -n "your-new-password" | gcloud secrets create postgres-prod-password \
  --data-file=- \
  --project=honest-sanbou-app-prod

# GCP サービスアカウント鍵（JSON ファイル全体）
gcloud secrets create gcp-sa-prod-key \
  --data-file=secrets/gcp-sa-prod.json \
  --project=honest-sanbou-app-prod

# IAP Audience
echo -n "your-iap-audience" | gcloud secrets create iap-audience-prod \
  --data-file=- \
  --project=honest-sanbou-app-prod
```

#### 7.2 アプリケーションコードの変更

```python
# app/backend/core_api/app/config.py
from google.cloud import secretmanager

def get_secret(secret_id: str) -> str:
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.getenv("GCP_PROJECT_ID")
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

# 使用例
# POSTGRES_PASSWORD = get_secret("postgres-prod-password")  # 例
```

**所要時間**: 4時間  
**影響範囲**: 全バックエンドサービス（段階的移行可能）

---

### Priority 8: GitHub Advanced Security の有効化

```bash
# GitHub リポジトリ設定
# https://github.com/torotorokou/sanbou_app/settings/security_analysis

# 有効化する機能:
# ✅ Dependency graph
# ✅ Dependabot alerts
# ✅ Dependabot security updates
# ✅ Secret scanning (private repo の場合、GitHub Advanced Security が必要)
# ✅ Code scanning (CodeQL)
```

**所要時間**: 10分  
**影響範囲**: なし（検出のみ）

---

### Priority 9: アクセスログの監視設定

#### 9.1 Cloud Logging でアラート作成

```bash
# 不正アクセスパターンの検出
# - 本番 DB への不審な接続試行
# - IAP 認証失敗の急増
# - GCS バケットへの大量アクセス

# Cloud Console → Logging → Logs-based metrics → Create metric
```

#### 9.2 通知設定

```bash
# Email / Slack への通知
gcloud alpha monitoring policies create \
  --notification-channels=<CHANNEL_ID> \
  --display-name="Sanbou App Security Alert" \
  --condition-display-name="Suspicious DB Access" \
  ...
```

**所要時間**: 2時間  
**影響範囲**: なし（モニタリングのみ）

---

## 📊 長期的な対応（優先度: 低〜中）

### Priority 10: 定期的な認証情報ローテーション

- **頻度**: 90日ごと
- **対象**: DB パスワード、GCP 鍵、API キー
- **自動化**: Terraform + Secret Manager でローテーション

### Priority 11: 監査ログの定期レビュー

- **頻度**: 週次
- **対象**: PostgreSQL アクセスログ、GCP Audit Logs
- **ツール**: Cloud Logging Insights

### Priority 12: 侵入テストの実施

- **頻度**: 年次
- **対象**: 本番環境全体
- **実施者**: 外部セキュリティ監査会社

---

## 🔧 今回導入したセーフティ機能

### 1. Pre-commit フック ✅

**機能**:
- env/ と secrets/ の実設定ファイル検出
- パスワード、API キーなど機密情報パターン検出
- commit 前にブロック

**場所**: `.git/hooks/pre-commit`

**テスト**:
```bash
# テスト用ファイルを作成
echo "TEST" > env/.env.test

# 誤って追加
git add env/.env.test

# commit を試みる（ブロックされるはず）
git commit -m "test"
# ❌ エラー: 機密ファイルを commit しようとしています
```

### 2. Git 履歴削除スクリプト ✅

**機能**:
- git-filter-repo で安全に履歴削除
- 削除前の確認プロンプト
- リモート復元の自動化

**場所**: `scripts/cleanup_git_history.sh`

**実行**:
```bash
bash scripts/cleanup_git_history.sh
```

### 3. .gitignore の強化 ✅

**変更内容**:
```gitignore
# Before
env/*                    # ファイルのみ除外（不十分）

# After
env/                     # ディレクトリ自体を除外
!env/.env.example        # テンプレートのみ許可
```

---

## 📋 実行チェックリスト

### 即座に実行（今日中）

- [ ] **Priority 1**: 本番 DB パスワード変更（10分）
- [ ] **Priority 2**: GCP サービスアカウント鍵再発行（15分）
- [ ] **Priority 3**: Git 履歴削除 + 強制プッシュ（30分）
- [ ] **Priority 4**: リポジトリを private に変更（2分）

**合計所要時間**: 約1時間

### 24時間以内

- [ ] **Priority 5**: ステージング環境のパスワード変更（25分）
- [ ] **Priority 6**: IAP 設定確認（10分）

**合計所要時間**: 約35分

### 1週間以内

- [ ] **Priority 7**: Secret Manager 移行（4時間）
- [ ] **Priority 8**: GitHub Advanced Security 有効化（10分）
- [ ] **Priority 9**: アクセスログ監視設定（2時間）

**合計所要時間**: 約6時間

---

## 🚨 緊急時の連絡先

```
セキュリティインシデント担当: <連絡先>
GCP プロジェクトオーナー: <連絡先>
GitHub Organization オーナー: <連絡先>
```

---

## 📞 次のステップ

**今すぐ実行してください**:

```bash
# Step 1: 本番 DB パスワード変更
ssh k_tsuchida@34.180.102.141
# (上記 Priority 1 の手順を実施)

# Step 2: GCP 鍵再発行
gcloud iam service-accounts keys list --iam-account=...
# (上記 Priority 2 の手順を実施)

# Step 3: Git 履歴削除
cd /home/koujiro/work_env/22.Work_React/sanbou_app
bash scripts/cleanup_git_history.sh
# (上記 Priority 3 の手順を実施)

# Step 4: GitHub リポジトリを private に
# https://github.com/torotorokou/sanbou_app/settings
# (上記 Priority 4 の手順を実施)
```

**完了したら**:
このドキュメントの実行チェックリストに ✅ をつけてください。

---

**最終更新**: 2025-12-06  
**ステータス**: 🔴 緊急対応必要  
**担当者**: k_tsuchida
