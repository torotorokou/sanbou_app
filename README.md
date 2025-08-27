
# sanbou_app

フロントエンド（Vite + React）と複数のFastAPIサービス、PostgreSQL、NginxをDocker Composeで統合したWebアプリです。

---

## すぐに起動する（Quick Start）

前提（ローカル開発・Linux想定）

- Docker / Docker Compose v2 がインストール済み
- make が利用可能

手順（開発環境: dev）

1) 環境変数ファイルを用意

   - 必須: `env/.env.dev` を作成
   - 例（必要に応じて調整）:

     ```env
     POSTGRES_USER=postgres
     POSTGRES_PASSWORD=postgres
     POSTGRES_DB=sanbou
     POSTGRES_PORT=5432

     # 開発用ポート（衝突時は変更可）
     FRONTEND_PORT=5173
     AI_API_PORT=8001
     LEDGER_API_PORT=8002
     SQL_API_PORT=8003
     RAG_API_PORT=8004
     ```

   - GCP を使う場合はサービスアカウント鍵を `secrets/gcs-key.json` に配置（devは任意、stg/prodは必須）

2) コンテナを起動

   - コマンド:

     ```bash
     make up ENV=dev
     ```

3) アクセス

   - Frontend: http://localhost:5173
   - AI API: http://localhost:8001/docs
   - Ledger API: http://localhost:8002/docs
   - SQL API: http://localhost:8003/docs
   - RAG API: http://localhost:8004/docs

4) 停止・ログ・再ビルド

   - 停止: `make down ENV=dev`
   - ログ: `make logs ENV=dev`（Ctrl+Cで離脱）
   - 再ビルド: `make rebuild ENV=dev`

---

## ステージング/本番での起動（stg/prod）

1) 環境変数ファイルを用意

- `env/.env.stg` または `env/.env.prod` を作成
- 初回の `make up` 実行時、`OPENAI_API_KEY` と `GEMINI_API_KEY` を対話入力すると `secrets/.env.<ENV>.secrets` に安全に保存されます
- GCP利用時は `secrets/gcs-key.json` を必ず配置

2) 起動

```bash
make up ENV=stg
# もしくは
make up ENV=prod
```

3) Nginx（エッジ）

- stg/prod は Nginx プロファイル（edge）で起動し、80/443 を公開
- 証明書と設定を配置:
  - `my-project/nginx/certs/*`（鍵/証明書）
  - `my-project/nginx/conf.d/*.conf`（仮想ホスト設定）

---

## よくあるエラーと対処

- envファイルが見つからない
  - `env/.env.dev`（または `.env.stg`/`.env.prod`）を作成してから `make up ENV=<env>` を実行
- ポート競合
  - `env/.env.<env>` の `FRONTEND_PORT`, `AI_API_PORT` などを空いている番号に変更
- `secrets/gcs-key.json not found`
  - GCP連携が必須の環境（stg/prod）ではファイルを配置。devでは警告のみ

---

## プロジェクト構成（簡略）

- `my-project/frontend`: フロントエンド（Vite + React）
- `my-project/backend/*_api`: 各FastAPIサービス（ai/ledger/sql/rag）
- `my-project/nginx`: 逆プロキシ設定と証明書
- `config`: CSV/レポート等の設定群
- `dbdata`: PostgreSQLデータ永続化用ボリューム
- `docker-compose.yml`: 本番相当のベース設定
- `docker-compose.override.yml`: 開発用の上書き設定（ホットリロードなど）
- `makefile`: 起動/停止/再ビルドなどの補助

---

## 補足（開発の進め方）

- 日常操作は `make up|down|logs|rebuild ENV=dev` が基本
- 各サービスの詳細は `my-project/backend/*/README.md` や `frontend/README.md`（存在する場合）を参照
- 機密情報（APIキー・鍵ファイル・DBデータ）は必ず git 管理外（`.gitignore` 済）

---

## サポート

不明点や要望があれば、プロジェクト管理者まで連絡してください。

---

## Docker 最適化 (2025-08)

本リポジトリはコンテナイメージサイズ削減 / セキュリティ向上 / ビルド時間短縮を目的に以下の改善を実施しました。

### 変更概要

- ベースイメージ統一
  - Frontend: `node:20-slim` (builder) + `nginx:alpine` (runtime)
  - Backend (FastAPI 各種): `python:3.11-slim` multi-stage (builder: wheel 生成 / runtime: 非root)
- Multi-stage build 導入
  - `pip wheel` による依存レイヤーキャッシュ化
  - runtime へは wheel インストール済み最小セットのみコピー
  - frontend は dist のみ nginx へ配置
- キャッシュ最適化
  - BuildKit 対応 `--mount=type=cache` を pip / npm へ適用
  - lockfile (`package-lock.json` / `requirements.txt`) ベースの再現性
- .dockerignore 強化
  - `node_modules`, `dist`, `tests`, `__pycache__`, `.env*`, logs などを除外し context 軽量化
- セキュリティ
  - 全 FastAPI サービス / frontend runtime を非 root 実行 (appuser / nginx)
  - `--no-install-recommends` / apt キャッシュ削除の徹底
  - Python 環境: `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`
- HEALTHCHECK 追加 (各 API / frontend)
- Compose での image 命名方針: `${REGISTRY:-local}/sanbou-<service>:<tag>`

### 期待効果 (目安)

- Frontend runtime イメージ: 50–80MB 台 (nginx:alpine + dist のみ)
- API runtime イメージ: 180–250MB 以内 (依存状況により変動 / LibreOffice を含む ledger_api は上限付近の可能性)
- 2回目以降のビルドは wheel / npm ci キャッシュで高速化

### ビルド方法

例: (REGISTRY 未指定ローカルビルド)

```bash
docker build -t local/sanbou-frontend:dev -f my-project/frontend/Dockerfile my-project/frontend
docker build -t local/sanbou-ai-api:dev -f my-project/backend/ai_api/Dockerfile my-project/backend/ai_api
```

複数サービス並列ビルド (GNU make + BuildKit 利用例):

```bash
DOCKER_BUILDKIT=1 docker compose build --parallel
```

### 実行 (開発)

従来通り:

```bash
make up ENV=dev
```

### ロールバック手順

1. Git でこの変更コミットを revert (`git revert <commit-hash>`) する
2. 旧 Dockerfile / .dockerignore / README 状態へ戻る
3. `docker compose build --no-cache` で再ビルドし挙動確認

もしくは一時的に特定サービスだけ旧版を使いたい場合:

```bash
docker build -t local/sanbou-ai-api:rollback -f my-project/backend/ai_api/Dockerfile.prev my-project/backend/ai_api
```
(
旧 Dockerfile を `Dockerfile.prev` として保管している想定。無い場合は Git 履歴から復元)

### 今後の追加改善候補

- Slim LibreOffice / unoconv 代替の検証 (ledger_api サイズさらなる削減)
- `requirements.txt` を `pip-tools` で lock 化
- マルチプラットフォーム (linux/amd64, arm64) ビルド対応
- Trivy / Grype を用いた CI の脆弱性スキャン

---
