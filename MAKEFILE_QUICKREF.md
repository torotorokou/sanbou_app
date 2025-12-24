# Makefile クイックリファレンス

> 詳細: [docs/infrastructure/MAKEFILE_GUIDE.md](./docs/infrastructure/MAKEFILE_GUIDE.md)

## 🚀 基本コマンド


# イメージを事前に pull して起動（VM環境向け）
# ※ `vm_stg` / `vm_prod` では `make up` 実行時にデフォルトで `pull` が実行されます。
#    これを無効化するには `PULL=0` を指定します: `make up ENV=vm_stg PULL=0`

# pull のみ実行
make pull ENV=local_dev
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

make pull ENV=vm_stg
# 補足: `vm_stg` はデフォルトで `make up` 時に `docker compose pull` されます。
# 事前に手動で pull する場合は: `make pull ENV=vm_stg`
```bash
# ログ確認（全サービス）
make logs ENV=local_dev

# 特定サービスのログ
make logs ENV=local_dev S=core_api

# コンテナ一覧
make ps ENV=local_dev

make pull ENV=vm_prod
# 補足: `vm_prod` はデフォルトで `make up` 時に `docker compose pull` されます。
# 事前に手動で pull する場合は: `make pull ENV=vm_prod`
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

### 初回環境構築（DB 権限システムのセットアップ）

**⚠️ 新規環境または権限エラーが頻発する場合のみ実行**

```bash
# 1. バックアップ取得（既存環境の場合）
make backup ENV=local_dev

# 2. DB 権限システム構築（全ステップ一括）
make db-fix-ownership ENV=local_dev

# 3. 検証
make db-verify-ownership ENV=local_dev

# 4. マイグレーション適用
make al-up-env ENV=local_dev
```

**実行内容**:
- `sanbou_owner` (NOLOGIN) ロール作成
- 全スキーマ・テーブル・シーケンスの owner を統一
- RW/RO スキーマごとの適切な権限付与
- DEFAULT PRIVILEGES 設定（新規オブジェクトへの自動権限付与）

**目的**: 「permission denied for sequence」等の権限エラーを根絶

詳細: [ops/db/README.md](./ops/db/README.md)

### 通常運用（マイグレーション）

**⚠️ 初回構築後は、通常これだけ実行すればOK**

```bash
# マイグレーション適用（DB Bootstrap を自動実行）
make al-up-env ENV=local_dev

# マイグレーション状態確認
make al-cur-env ENV=local_dev

# マイグレーション履歴
make al-hist-env ENV=local_dev
```

### トラブルシューティング（DB 権限）

```bash
# 段階的に権限を修正（問題箇所のみ再実行）
make db-fix-ownership ENV=local_dev STEP=1  # ロール作成
make db-fix-ownership ENV=local_dev STEP=2  # owner 移管
make db-fix-ownership ENV=local_dev STEP=3  # 権限付与
make db-fix-ownership ENV=local_dev STEP=4  # デフォルト権限設定

# 権限状態の詳細確認
make db-verify-ownership ENV=local_dev

# Legacy Bootstrap（通常は不要、al-up-env が自動実行）
make db-bootstrap-roles-env ENV=local_dev
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

# 例: STGの最新タグを PROD の特定バージョンへ昇格
make promote-stg-to-prod PROMOTE_SRC_TAG=stg-latest PROMOTE_DST_TAG=prod-v1.2.3

# または直接ビルド
# make publish-prod-images PROD_IMAGE_TAG=prod-latest
NO_CACHE=1 PULL=1 make publish-stg-images-from-ref GIT_REF=v1.2.3-stg.4
# NO_CACHE=1 PULL=1 make publish-stg-images STG_IMAGE_TAG=stg-latest

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
   ```bash
   make backup ENV=vm_prod
   ```
3. **初回のみ**: DB 権限システム構築
   ```bash
   make db-fix-ownership ENV=vm_prod
   make db-verify-ownership ENV=vm_prod
   ```
4. **ローカルPC**: イメージ昇格または直接ビルド
5. **ローカルPC**: env/.env.vm_prod の IMAGE_TAG 更新
6. **ローカルPC**: Git commit & push
7. **VM**: `git pull origin main`
8. **VM**: `make down ENV=vm_stg` （必要に応じて）
9. **VM**: `make up ENV=vm_prod`
10. **VM**: `make al-up-env ENV=vm_prod`
11. **動作確認**: `curl https://example.com/health`

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

#### `permission denied for sequence` または権限エラー

```bash
# DB 権限システムを再構築
make db-fix-ownership ENV=vm_stg
make db-verify-ownership ENV=vm_stg
```

#### `role "app_readonly" does not exist`

```bash
# Legacy Bootstrap を手動実行（通常は al-up-env が自動実行）
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
