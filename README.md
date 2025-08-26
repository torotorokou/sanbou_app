
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
