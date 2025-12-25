# Makefile 運用ガイド

> **✅ 最終更新**: 2025年12月12日 - migrations_v2 が標準マイグレーションシステムになりました

## 📋 目次

1. [概要](#概要)
2. [環境の種類](#環境の種類)
3. [基本操作](#基本操作)
4. [VM環境への移行ガイド](#vm環境への移行ガイド)
5. [Alembic マイグレーション](#alembic-マイグレーション)
6. [バックアップ・リストア](#バックアップリストア)
7. [イメージビルド・デプロイ](#イメージビルドデプロイ)
8. [トラブルシューティング](#トラブルシューティング)

---

## 概要

このMakefileは、sanbou_appの全環境（開発・ステージング・本番・デモ）の
Docker Compose操作を統一的に管理するためのツールです。

### 特徴

- **環境変数ベース**: `ENV` パラメータで環境を切り替え
- **冪等性**: 何度実行しても安全な設計
- **VM対応**: ローカルとVM環境の両方をサポート
- **自動化**: DB bootstrap、マイグレーション、デプロイを自動化
- **migrations_v2**: 標準マイグレーションシステム（legacy migrations/ は削除済み）

---

## 環境の種類

| ENV名        | 説明                | 用途           | ビルド | イメージソース    |
| ------------ | ------------------- | -------------- | ------ | ----------------- |
| `local_dev`  | ローカル開発環境    | 開発・デバッグ | ⭕     | ローカルビルド    |
| `local_demo` | ローカルデモ環境    | デモ・検証     | ⭕     | ローカルビルド    |
| `vm_stg`     | GCP VM ステージング | 統合テスト     | ❌     | Artifact Registry |
| `vm_prod`    | GCP VM 本番環境     | 本番運用       | ❌     | Artifact Registry |

### 環境ごとの設定ファイル

```
env/
├── .env.common           # 全環境共通
├── .env.local_dev        # ローカル開発
├── .env.local_demo       # ローカルデモ
├── .env.vm_stg          # VM ステージング
└── .env.vm_prod         # VM 本番

secrets/
├── .env.local_dev.secrets
├── .env.vm_stg.secrets
└── .env.vm_prod.secrets
```

---

## 基本操作

### 環境の起動・停止

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

### ログ確認

```bash
# 全サービスのログ
make logs ENV=local_dev

# 特定サービスのログ
make logs ENV=local_dev S=core_api

# ログをフォロー
make logs ENV=local_dev S=ai_api
```

### コンテナ状態確認

```bash
# 実行中のコンテナ一覧
make ps ENV=local_dev

# ヘルスチェック
make health ENV=local_dev

# 設定確認
make config ENV=local_dev
```

---

## VM環境への移行ガイド

### 🚀 ステージング環境（vm_stg）への移行

#### **前提条件**

- GCP VMインスタンスが作成済み
- Tailscale VPN経由でVMにアクセス可能
- Docker & Docker Composeがインストール済み
- gcloud CLIがインストール・認証済み（ローカルPC）

#### **Step 1: ローカルPCでイメージをビルド・プッシュ**

```bash
# ワンタイム: gcloud 認証設定
make gcloud-auth-docker

# STG用イメージをビルド・プッシュ
make publish-stg-images STG_IMAGE_TAG=stg-20251212

# イメージ確認
make check-stg-images STG_IMAGE_TAG=stg-20251212
```

#### **Step 2: env/.env.vm_stg の IMAGE_TAG を更新**

```bash
# env/.env.vm_stg
IMAGE_TAG=stg-20251212
```

コミット・プッシュして、VM上で最新を取得します。

#### **Step 3: VM上でセットアップ**

```bash
# VM にログイン
ssh vm-stg  # または Tailscale経由

# リポジトリをclone（初回のみ）
git clone <リポジトリURL> ~/sanbou_app
cd ~/sanbou_app

# 最新コードを取得
git pull origin main

# gcloud 認証（初回のみ）
gcloud auth login
gcloud auth configure-docker asia-northeast1-docker.pkg.dev

# 環境起動
make up ENV=vm_stg

# 動作確認
make health ENV=vm_stg
curl -I http://localhost/health
```

#### **Step 4: DBマイグレーション実行**

```bash
# DB Bootstrap（ロール・権限設定）
make db-bootstrap-roles-env ENV=vm_stg

# Alembic マイグレーション
make al-up-env ENV=vm_stg

# マイグレーション状態確認
make al-cur-env ENV=vm_stg
```

#### **Step 5: 動作確認**

```bash
# VM内から
curl http://localhost/
curl http://localhost/api/v1/health

# ローカルPCから（Tailscale経由）
# http://<VM-Tailscale-IP>/
# 例: http://100.119.243.45/
```

---

### 🔥 本番環境（vm_prod）への移行

#### **前提条件**

- GCP VMインスタンスが作成済み
- Cloud Load Balancer + IAP設定済み
- ドメイン（example.com）がLBに向いている
- Docker & Docker Composeがインストール済み

#### **Step 1: ローカルPCでイメージをビルド・プッシュ**

```bash
# PROD用イメージをビルド・プッシュ
make publish-prod-images PROD_IMAGE_TAG=prod-20251212

# または、STGからの昇格（推奨）
make promote-stg-to-prod \
  PROMOTE_SRC_TAG=stg-20251212 \
  PROMOTE_DST_TAG=prod-20251212

# イメージ確認
make check-prod-images PROD_IMAGE_TAG=prod-20251212
```

#### **Step 2: env/.env.vm_prod の IMAGE_TAG を更新**

```bash
# env/.env.vm_prod
IMAGE_TAG=prod-20251212
```

コミット・プッシュして、VM上で最新を取得します。

#### **Step 3: VM上でセットアップ**

```bash
# VM にログイン
gcloud compute ssh vm-prod --project=your-project-id

# リポジトリをclone（初回のみ）
git clone <リポジトリURL> ~/sanbou_app
cd ~/sanbou_app

# 最新コードを取得
git pull origin main

# gcloud 認証（初回のみ）
gcloud auth login
gcloud auth configure-docker asia-northeast1-docker.pkg.dev

# 既存環境を停止（vm_stgが起動中の場合）
make down ENV=vm_stg

# 本番環境起動
make up ENV=vm_prod

# 動作確認
make health ENV=vm_prod
curl -I http://localhost/health
```

#### **Step 4: DBマイグレーション実行**

⚠️ **本番環境では慎重に実施してください**

```bash
# バックアップ（必須）
make backup ENV=vm_prod BACKUP_DIR=/path/to/backup

# DB Bootstrap
make db-bootstrap-roles-env ENV=vm_prod

# Alembic マイグレーション（ドライラン確認後）
make al-cur-env ENV=vm_prod
make al-up-env ENV=vm_prod

# 確認
make al-cur-env ENV=vm_prod
```

#### **Step 5: 動作確認**

```bash
# VM内から
curl http://localhost/
curl http://localhost/api/v1/health

# 外部から（LB + IAP経由）
# https://example.com/
```

---

## Alembic マイグレーション

### 基本操作

```bash
# マイグレーションファイル作成（手動）
make al-rev MSG="add user table" ENV=local_dev

# マイグレーションファイル作成（自動検出）
make al-rev-auto MSG="auto detect changes" ENV=local_dev

# マイグレーション適用（local_dev）
make al-up ENV=local_dev

# マイグレーション適用（ENV指定）
make al-up-env ENV=vm_stg

# マイグレーション状態確認
make al-cur ENV=local_dev
make al-cur-env ENV=vm_stg

# マイグレーション履歴
make al-hist ENV=local_dev
make al-hist-env ENV=vm_prod

# 1つ戻す
make al-down ENV=local_dev
make al-down-env ENV=vm_stg
```

### 新規環境での自動構築（推奨）

`al-up-env` を実行すると、新規環境では自動的に以下の順序で実行されます：

1. **db-ensure-baseline-env**: スキーマ・テーブル構造の適用（初回のみ、冪等）
   - marker table (`public.schema_baseline_meta`) で適用済み判定
   - `app/backend/core_api/migrations_v2/sql/schema_baseline.sql` を使用
   - vm_prod では `FORCE=1` 必須（誤操作防止）
2. **db-bootstrap-roles-env**: app_readonly ロールと権限の設定（冪等）
3. **alembic upgrade head**: 差分マイグレーション

**使用例**:

```bash
# 新規環境（自動で器まで作成）
make al-up-env ENV=vm_stg

# 本番環境（初回のみFORCE=1必須）
make al-up-env ENV=vm_prod FORCE=1

# 既存環境（baselineスキップ、差分だけ適用）
make al-up-env ENV=local_dev
```

**注意事項**:

- baseline適用後は `stg`, `mart`, `ref`, `kpi`, `tmp` 等のスキーマ・テーブルが作成されます
- 中途半端な状態（stgだけ存在等）では明示的にボリューム削除が必要です

手動実行する場合：

```bash
make db-ensure-baseline-env ENV=vm_stg
make db-bootstrap-roles-env ENV=local_dev
make db-bootstrap-roles-env ENV=vm_stg
make db-bootstrap-roles-env ENV=vm_prod
```

---

## バックアップ・リストア

### バックアップ

```bash
# local_dev のバックアップ
make backup ENV=local_dev

# カスタムディレクトリ指定
make backup ENV=vm_prod \
  BACKUP_DIR=/path/to/backup \
  PGDB=sanbou_prod

# 出力例: backups/sanbou_dev_local_dev_2025-12-12_143025.dump
```

### リストア

#### dumpファイルから

```bash
# .dumpファイルからリストア
make restore-from-dump \
  ENV=local_dev \
  DUMP=backups/sanbou_dev_2025-12-12_143025.dump

# 別環境へのリストア
make restore-from-dump \
  ENV=local_demo \
  DUMP=backups/sanbou_dev_local_dev_2025-12-12_143025.dump \
  PGDB=sanbou_demo
```

#### SQLファイルから

```bash
# .sqlファイルからリストア
make restore-from-sql \
  ENV=local_demo \
  SQL=backups/pg_all_2025-12-03.sql
```

---

## イメージビルド・デプロイ

### ローカル開発

```bash
# 通常起動（自動ビルド）
make up ENV=local_dev

# nginx付き起動（本番に近い構成）
make dev-with-nginx
# アクセス: http://localhost:8080
```

### ステージング環境

```bash
# 【ローカルPC】イメージビルド・プッシュ
make publish-stg-images STG_IMAGE_TAG=stg-20251212

# 【VM】イメージプル・起動
make up ENV=vm_stg
```

### 本番環境

#### パターン1: 直接ビルド（非推奨）

```bash
# 【ローカルPC】
make publish-prod-images PROD_IMAGE_TAG=prod-20251212

# 【VM】
make up ENV=vm_prod
```

#### パターン2: STGから昇格（推奨）

```bash
# 【ローカルPC】STGイメージをPRODにコピー
make promote-stg-to-prod \
  PROMOTE_SRC_TAG=stg-20251212 \
  PROMOTE_DST_TAG=prod-20251212

# 【VM】env/.env.vm_prod を更新してpush

# 【VM】
cd ~/sanbou_app
git pull origin main
make down ENV=vm_stg  # 必要に応じて
make up ENV=vm_prod
```

### ビルドオプション

```bash
# キャッシュなし＋最新ベースイメージ
NO_CACHE=1 PULL=1 make publish-stg-images STG_IMAGE_TAG=stg-20251212

# 本番環境でも同様
NO_CACHE=1 PULL=1 make publish-prod-images PROD_IMAGE_TAG=prod-20251212
```

---

## トラブルシューティング

### よくある問題

#### 1. `role "app_readonly" does not exist` エラー

**原因**: DB bootstrapが未実行

**解決策**:

```bash
make db-bootstrap-roles-env ENV=vm_stg
make al-up-env ENV=vm_stg
```

#### 2. ポート80が既に使用されている

**原因**: vm_stg と vm_prod が同時起動している

**解決策**:

```bash
# どちらか片方をdown
make down ENV=vm_stg
make up ENV=vm_prod
```

#### 3. イメージがpullできない

**原因**: gcloud認証が未設定

**解決策**:

```bash
# ローカルPC
make gcloud-auth-docker

# VM
gcloud auth login
gcloud auth configure-docker asia-northeast1-docker.pkg.dev
```

#### 4. マイグレーションが失敗する

**原因**: スキーマ不整合、権限不足

**解決策**:

```bash
# 現在の状態確認
make al-cur-env ENV=vm_stg

# bootstrap再実行
make db-bootstrap-roles-env ENV=vm_stg

# マイグレーション履歴確認
make al-hist-env ENV=vm_stg

# 必要に応じてstamp（既存DBの場合）
make al-stamp-env ENV=vm_stg REV=<REVISION_ID>
```

#### 5. nginxが502 Bad Gatewayを返す

**原因**: バックエンドサービスが起動していない

**解決策**:

```bash
# コンテナ状態確認
make ps ENV=vm_prod

# ログ確認
make logs ENV=vm_prod S=core_api

# 再起動
make restart ENV=vm_prod
```

### デバッグコマンド

```bash
# 環境変数・設定確認
make config ENV=vm_stg

# コンテナ内でシェル起動
docker compose -p vm_stg exec core_api bash

# DBに直接接続
docker compose -p vm_stg exec db psql -U dbuser -d sanbou_stg

# ネットワーク確認
docker compose -p vm_stg exec nginx curl http://core_api:8000/health
```

---

## セキュリティスキャン（Trivy）

```bash
# ローカルイメージスキャン
make scan-local-images

# STGイメージスキャン
make scan-stg-images STG_IMAGE_TAG=stg-20251212

# PRODイメージスキャン
make scan-prod-images PROD_IMAGE_TAG=prod-20251212
```

---

## VM環境での運用ルール

### ⚠️ 重要な制約

1. **vm_stg と vm_prod は同時起動不可**

   - ポート80が競合するため、必ず片方をdownしてから起動

2. **イメージはローカルでビルド**

   - VM上ではビルドせず、Artifact Registryからpull

3. **マイグレーションは慎重に**

   - 本番環境では必ずバックアップを取ってから実施

4. **secrets ファイルは手動配置**
   - `secrets/.env.vm_stg.secrets`
   - `secrets/.env.vm_prod.secrets`
   - Gitにはコミットしない

### デプロイチェックリスト

#### ステージング

- [ ] ローカルでイメージビルド・プッシュ完了
- [ ] env/.env.vm_stg の IMAGE_TAG 更新
- [ ] Git push完了
- [ ] VM上で git pull 完了
- [ ] make up ENV=vm_stg 成功
- [ ] make health ENV=vm_stg 正常
- [ ] DBマイグレーション完了
- [ ] 動作確認完了

#### 本番

- [ ] STGでの十分なテスト完了
- [ ] 本番DBバックアップ取得完了
- [ ] イメージプッシュ（またはSTGから昇格）完了
- [ ] env/.env.vm_prod の IMAGE_TAG 更新
- [ ] メンテナンスモード設定（必要に応じて）
- [ ] 本番環境デプロイ
- [ ] DBマイグレーション実行
- [ ] ヘルスチェック・動作確認
- [ ] メンテナンスモード解除

---

## 参考リンク

- [Alembic公式ドキュメント](https://alembic.sqlalchemy.org/)
- [Docker Compose公式ドキュメント](https://docs.docker.com/compose/)
- [GCP Artifact Registry](https://cloud.google.com/artifact-registry/docs)
- [Trivy公式サイト](https://aquasecurity.github.io/trivy/)

---

## 更新履歴

| 日付       | 変更内容                    |
| ---------- | --------------------------- |
| 2025-12-12 | 初版作成、VM移行ガイド追加  |
| 2025-12-12 | DB Bootstrap セクション追加 |
