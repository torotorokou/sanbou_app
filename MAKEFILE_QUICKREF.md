# Makefile クイックリファレンス

> 詳細: [docs/infrastructure/MAKEFILE_GUIDE.md](./docs/infrastructure/MAKEFILE_GUIDE.md)

## 🚀 基本コマンド

### 環境起動・停止

```bash
# 起動
make up ENV=local_dev

# 停止
make down ENV=local_dev

# 再起動
make restart ENV=local_dev

# 完全再ビルド
make rebuild ENV=local_dev
```

### ログ・状態確認

```bash
# ログ確認（全サービス）
make logs ENV=local_dev

# 特定サービスのログ
make logs ENV=local_dev S=core_api

# コンテナ一覧
make ps ENV=local_dev

# ヘルスチェック
make health ENV=local_dev
```

## 🌍 環境一覧

| ENV | 説明 | ビルド | イメージソース |
|-----|------|--------|----------------|
| `local_dev` | ローカル開発 | ⭕ | ローカル |
| `local_demo` | ローカルデモ | ⭕ | ローカル |
| `vm_stg` | VMステージング | ❌ | Artifact Registry |
| `vm_prod` | VM本番 | ❌ | Artifact Registry |

## 🗄️ データベース操作

### バックアップ

```bash
make backup ENV=local_dev
# → backups/sanbou_dev_local_dev_YYYYMMDD_HHMMSS.dump
```

### リストア

```bash
make restore-from-dump ENV=local_dev DUMP=backups/xxx.dump
```

### マイグレーション

```bash
# DB Bootstrap（権限設定、冪等）
make db-bootstrap-roles-env ENV=local_dev

# マイグレーション適用（自動的にbootstrapも実行）
# ※ migrations_v2 を使用（legacy migrations/ は削除済み）
make al-up-env ENV=local_dev

# マイグレーション状態確認
make al-cur-env ENV=local_dev

# マイグレーション履歴
make al-hist-env ENV=local_dev
```

## 🏗️ イメージビルド・デプロイ

### ステージング

```bash
# 【ローカルPC】イメージビルド・プッシュ
make publish-stg-images STG_IMAGE_TAG=stg-20251212

# env/.env.vm_stg を更新
# IMAGE_TAG=stg-20251212

# 【VM】起動
make up ENV=vm_stg
make al-up-env ENV=vm_stg
```

### 本番

```bash
# 【ローカルPC】STGから昇格（推奨）
make promote-stg-to-prod \
  PROMOTE_SRC_TAG=stg-20251212 \
  PROMOTE_DST_TAG=prod-20251212

# または直接ビルド
make publish-prod-images PROD_IMAGE_TAG=prod-20251212

# env/.env.vm_prod を更新
# IMAGE_TAG=prod-20251212

# 【VM】起動
make up ENV=vm_prod
make al-up-env ENV=vm_prod
```

## 📋 VM環境移行チェックリスト

### ステージング環境構築

- [ ] GCP VM インスタンス作成済み
- [ ] Tailscale VPN 設定済み
- [ ] Docker & Docker Compose インストール済み
- [ ] gcloud CLI インストール・認証済み
- [ ] リポジトリ clone 済み
- [ ] `make gcloud-auth-docker` 実行済み
- [ ] `env/.env.vm_stg` 設定確認
- [ ] `secrets/.env.vm_stg.secrets` 配置済み

### デプロイ手順

1. **ローカルPC**: イメージビルド・プッシュ
2. **ローカルPC**: env/.env.vm_stg の IMAGE_TAG 更新
3. **ローカルPC**: Git commit & push
4. **VM**: `git pull origin main`
5. **VM**: `make up ENV=vm_stg`
6. **VM**: `make al-up-env ENV=vm_stg`
7. **動作確認**: `curl http://localhost/health`

### 本番環境構築

- [ ] GCP VM インスタンス作成済み
- [ ] Cloud Load Balancer + IAP 設定済み
- [ ] ドメイン設定済み
- [ ] Docker & Docker Compose インストール済み
- [ ] gcloud CLI インストール・認証済み
- [ ] リポジトリ clone 済み
- [ ] `make gcloud-auth-docker` 実行済み
- [ ] `env/.env.vm_prod` 設定確認
- [ ] `secrets/.env.vm_prod.secrets` 配置済み

### 本番デプロイ手順

1. **ステージング**: 十分なテスト実施
2. **本番DB**: バックアップ取得（必須）
3. **ローカルPC**: イメージ昇格または直接ビルド
4. **ローカルPC**: env/.env.vm_prod の IMAGE_TAG 更新
5. **ローカルPC**: Git commit & push
6. **VM**: `git pull origin main`
7. **VM**: `make down ENV=vm_stg` （必要に応じて）
8. **VM**: `make up ENV=vm_prod`
9. **VM**: `make al-up-env ENV=vm_prod`
10. **動作確認**: `curl https://example.com/health`

## ⚠️ 重要な注意事項

### VM環境の制約

1. **ポート競合**: vm_stg と vm_prod は同時起動不可（ポート80競合）
   ```bash
   # STGを起動する前にPRODを停止
   make down ENV=vm_prod
   make up ENV=vm_stg
   ```

2. **イメージソース**: VM環境ではローカルビルドせず Artifact Registry から pull

3. **マイグレーション**: 本番環境では必ずバックアップを取ってから実施

4. **secrets ファイル**: Git にコミットせず、VM に手動配置

### トラブルシューティング

#### `role "app_readonly" does not exist`

```bash
make db-bootstrap-roles-env ENV=vm_stg
make al-up-env ENV=vm_stg
```

#### `イメージが pull できない`

```bash
# 認証確認
gcloud auth login
make gcloud-auth-docker
```

#### `マイグレーションが失敗`

```bash
# 状態確認
make al-cur-env ENV=vm_stg
make al-hist-env ENV=vm_stg

# bootstrap再実行
make db-bootstrap-roles-env ENV=vm_stg
```

## 📚 詳細ドキュメント

完全なドキュメント・移行ガイド:
- [docs/infrastructure/MAKEFILE_GUIDE.md](./docs/infrastructure/MAKEFILE_GUIDE.md)

関連ドキュメント:
- [docs/development/ALEMBIC_GUIDE.md](./docs/development/ALEMBIC_GUIDE.md)
- [docs/infrastructure/DEPLOYMENT.md](./docs/infrastructure/DEPLOYMENT.md)
