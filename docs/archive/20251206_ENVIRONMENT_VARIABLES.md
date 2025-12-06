# 環境変数管理ガイド

## 概要

このプロジェクトでは、環境変数を `.env` ファイルで一元管理しています。
各サービス（core_api, forecast_worker, etc.）は `docker-compose.yml` の `env_file` ディレクティブを通じて環境変数を読み込みます。

## ファイル構造

```
env/
├── .env.common          # 全環境共通の設定
├── .env.local_dev       # ローカル開発環境（ホットリロード有効）
├── .env.local_stg       # ローカルSTG環境（nginx + 本番近似）
├── .env.vm_stg          # VM STG環境
├── .env.vm_prod         # VM 本番環境
└── .env.example         # サンプルファイル
```

## 読み込み順序

Docker Composeは以下の順序で環境変数を読み込みます：

1. `.env.common` - 共通設定
2. `.env.{環境名}` - 環境固有設定（上書き）
3. `docker-compose.yml` の `environment` セクション（最終的な上書き）

## 主要な環境変数

### データベース関連 (`.env.common`)

```bash
POSTGRES_USER=__SET_IN_ENV_SPECIFIC_FILE__
# POSTGRES_PASSWORD は secrets/.env.*.secrets で設定
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

> **注意**: 実際のユーザー名とパスワードは `secrets/.env.*.secrets` で設定してください。

### 各環境での設定 (`.env.{環境名}`)

```bash
POSTGRES_DB=sanbou_dev               # local_dev
POSTGRES_DB=sanbou_stg               # local_stg, vm_stg
POSTGRES_DB=sanbou_prod              # vm_prod

# DATABASE_URL は secrets/.env.*.secrets で設定
# 形式: postgresql://<USER>:<PASSWORD>@db:5432/<DB_NAME>
DATABASE_URL=__SET_IN_SECRETS__
```

### Pythonパス (`.env.common`)

```bash
# 標準APIサービス（ai_api, ledger_api, rag_api, manual_api）
APP_ROOT_DIR=/backend
PYTHONPATH=/backend

# Core API（BFF）
CORE_API_PYTHONPATH=/backend

# Forecast Worker（独立したワーカー）
FORECAST_WORKER_PYTHONPATH=/worker
```

### Core API設定 (`.env.{環境名}`)

```bash
# 内部APIのベースURL
RAG_API_BASE=http://rag_api:8000
LEDGER_API_BASE=http://ledger_api:8000
MANUAL_API_BASE=http://manual_api:8000
AI_API_BASE=http://ai_api:8000
```

### Forecast Worker設定 (`.env.{環境名}`)

```bash
# ジョブポーリング間隔（秒）
POLL_INTERVAL=3      # local_dev
POLL_INTERVAL=5      # vm_stg
POLL_INTERVAL=10     # vm_prod
```

### ポート設定 (`.env.local_dev`)

```bash
DEV_FRONTEND_PORT=5173
DEV_AI_API_PORT=8001
DEV_LEDGER_API_PORT=8002
DEV_CORE_API_PORT=8003
DEV_RAG_API_PORT=8004
DEV_MANUAL_API_PORT=8005
```

## Docker Compose での使用方法

### core_api の例

```yaml
services:
  core_api:
    env_file:
      - ../env/.env.common
      - ../env/.env.local_dev
    environment:
      - PYTHONPATH=${CORE_API_PYTHONPATH}
      - DATABASE_URL=${DATABASE_URL}
      - RAG_API_BASE=${RAG_API_BASE}
      - LEDGER_API_BASE=${LEDGER_API_BASE}
      - MANUAL_API_BASE=${MANUAL_API_BASE}
      - AI_API_BASE=${AI_API_BASE}
```

### forecast_worker の例

```yaml
services:
  forecast_worker:
    env_file:
      - ../env/.env.common
      - ../env/.env.local_dev
    environment:
      - PYTHONPATH=${FORECAST_WORKER_PYTHONPATH}
      - DATABASE_URL=${DATABASE_URL}
      - POLL_INTERVAL=${POLL_INTERVAL}
```

## 環境変数の確認方法

### コンテナ内の環境変数を確認

```bash
# core_api の環境変数
docker exec local_dev-core_api-1 env | grep -E "(PYTHONPATH|DATABASE_URL|RAG_API_BASE)"

# forecast_worker の環境変数
docker exec local_dev-forecast_worker-1 env | grep -E "(PYTHONPATH|DATABASE_URL|POLL_INTERVAL)"
```

### Docker Compose の最終設定を確認

```bash
make config ENV=local_dev
```

## 新しい環境変数の追加方法

### 1. 全環境共通の場合

`.env.common` に追加：

```bash
# === 新しい設定 ===
NEW_VARIABLE=default_value
```

### 2. 環境固有の場合

各環境ファイル（`.env.local_dev`, `.env.vm_stg`, `.env.vm_prod`）に追加：

```bash
# local_dev
NEW_VARIABLE=dev_value

# vm_stg
NEW_VARIABLE=stg_value

# vm_prod
NEW_VARIABLE=prod_value
```

### 3. docker-compose.yml に反映

必要に応じて `docker-compose.yml` の `environment` セクションに追加：

```yaml
environment:
  - NEW_VARIABLE=${NEW_VARIABLE}
```

## ベストプラクティス

### ✅ 推奨

- **共通設定は `.env.common` に**: すべての環境で同じ値を使う変数
- **環境差分は環境別ファイルに**: 環境ごとに異なる値（DB名、URL、ポーリング間隔など）
- **秘密情報は別管理**: API キーやパスワードは `secrets/` ディレクトリ、または環境変数で注入

### ❌ 非推奨

- **docker-compose.yml にハードコード**: 環境差分がある値を直接書くのは避ける
- **同じ変数を複数箇所で定義**: 上書きの順序が不明瞭になる
- **`.env` ファイルをGitにコミット**: `.env.example` のみコミット

## トラブルシューティング

### 環境変数が反映されない

```bash
# コンテナを完全に再作成
make down ENV=local_dev
make up ENV=local_dev

# または
docker-compose down
docker-compose up -d --force-recreate
```

### 環境変数の値が予期しない

```bash
# Docker Compose の最終設定を確認
docker-compose config

# または make コマンドで確認
make config ENV=local_dev
```

### データベース接続エラー

```bash
# DATABASE_URL が正しいか確認
docker exec local_dev-core_api-1 env | grep DATABASE_URL

# データベースコンテナの状態確認
docker ps --filter "name=db"
docker logs local_dev-db-1
```

## 参考リンク

- [Docker Compose Environment Variables](https://docs.docker.com/compose/environment-variables/)
- [プロジェクト Makefile](../makefile)
- [Core API README](../app/backend/core_api/README.md)
- [Forecast Worker README](../app/backend/forecast_worker/README.md)
