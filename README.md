
# sanbou_app

## 2025-09 環境拡張 (4 環境: dev / local_stg / vm_stg / prod)

| ENV      | 目的 | .env ファイル        | Compose ファイル                | Health URL                         | 備考 |
|----------|------|----------------------|---------------------------------|------------------------------------|------|
| dev      | ローカル開発 (ホットリロード) | `env/.env.dev`                  | `docker/docker-compose.dev.yml`    | http://localhost:8001/health | Vite + uvicorn reload |
| local_stg| STG 擬似 (nginx, HTTP)     | `env/.env.local_stg`            | `docker/docker-compose.stg.yml`    | http://stg.local/health      | `/etc/hosts` に `127.0.0.1 stg.local` |
| vm_stg   | VM 上 STG (将来 TLS)        | `env/.env.stg`                 | `docker/docker-compose.stg.yml`    | http://stg.sanbou-app.jp/health | nginx + 将来 443 有効化 |
| prod     | 本番                        | `env/.env.prod`                | `docker/docker-compose.prod.yml`   | https://sanbou-app.jp/health | 443 公開 |

統一 Nginx 設定: `app/nginx/conf.d/stg.conf` を local_stg / vm_stg で共用し、`server_name` をコメント切替。TLS はコメントアウト済みセクションを有効化して利用。

### make コマンド (ENV 指定対応)

```
make rebuild ENV=dev|local_stg|vm_stg|prod   # config → down → build --pull --no-cache → up → health
make up ENV=local_stg                        # 起動 (build あり)
make down ENV=vm_stg                         # 停止
make logs ENV=prod S=nginx                   # ログ (サービス指定可)
make restart ENV=dev                         # 再起動
make health ENV=local_stg                    # ヘルスチェック (curl/wget)
```

### local_stg 利用時の hosts 設定

```
sudo sh -c 'echo "127.0.0.1 stg.local" >> /etc/hosts'
```

### 典型的な検証手順

1. 必要な `.env` 作成: `cp env/.env.example env/.env.local_stg` などで雛形作成し値調整
2. `make rebuild ENV=local_stg`
3. `curl -I http://stg.local/health` (ない場合は `make logs ENV=local_stg S=nginx` で確認)
4. ブラウザで http://stg.local/ を開く

他環境も同様に `ENV=` を差し替え

### ロールバック手順 (今回拡張を取り消す場合)

1. 追加ファイル削除:
  - `env/.env.dev`
  - `env/.env.local_stg`
  - `env/.env.example`
  - `app/nginx/conf.d/stg.conf`
2. `docker/docker-compose.stg.yml` の `nginx` サービス volume を 元の `../app/nginx/conf.d.stg:/etc/nginx/conf.d` へ戻す
3. Makefile を Git 履歴で前の版に戻す (`git checkout <old_commit> -- makefile` もしくは `git revert`)
4. README の本節を削除
5. `make rebuild ENV=stg` / `make up ENV=dev` で従来フロー確認

最小差分化のため既存サービス名・ポート・ボリュームは変更していません。`dev` 環境ヘルスチェックは実際の公開ポート (ai_api:8001) に合わせて `http://localhost:8001/health` としています (既存構成では 8000 未公開のため)。


フロントエンド（Vite + React）と複数のFastAPIサービス、PostgreSQL、NginxをDocker Composeで統合したWebアプリです。

2025-09 更新: 環境分離を明確化
- dev: Vite dev サーバ + FastAPI (uvicorn --reload) を直接公開。Nginx コンテナは起動しない。
- stg/prod: Nginx (edge プロファイル) が React ビルド成果物を配信し、FastAPI 群をリバースプロキシ。
- DB(PostgreSQL) を共通サービス `db` として追加。

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

3) アクセス (dev)

  - Frontend: http://localhost:5173
  - AI API: http://localhost:8001/docs
  - Ledger API: http://localhost:8002/docs
  - SQL API: http://localhost:8003/docs
  - RAG API: http://localhost:8004/docs
  - Postgres: localhost:5432 (HOST 側からは `psql -h localhost -U myuser myapp`)

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

2) 起動 (Nginx を有効化する edge プロファイルを利用)

```bash
COMPOSE_PROFILES=edge make up ENV=stg
# もしくは本番
COMPOSE_PROFILES=edge make up ENV=prod
```

3) Nginx（エッジ）

- stg/prod は Nginx プロファイル（edge）で起動し、80/443 を公開
- 証明書と設定を配置:
  - `app/nginx/certs/*`（鍵/証明書）
  - `app/nginx/conf.d/*.conf`（仮想ホスト設定）

---

## よくあるエラーと対処

- envファイルが見つからない
  - `env/.env.dev`（または `.env.stg`/`.env.prod`）を作成してから `make up ENV=<env>` を実行
- ポート競合
  - `env/.env.<env>` の `FRONTEND_PORT`, `AI_API_PORT` などを空いている番号に変更
  - (stg) Nginx で 8080/8443 衝突時は一時的に環境変数指定: `STG_NGINX_HTTP_PORT=18080 STG_NGINX_HTTPS_PORT=18443 make up ENV=stg`
  - 恒久対応するなら `.env.stg` に `STG_NGINX_HTTP_PORT=18080` / `STG_NGINX_HTTPS_PORT=18443` を追記
  - 8080 を占有しているプロセス調査: `ss -ltnp | grep :8080` または `lsof -iTCP:8080 -sTCP:LISTEN`
  - 不要な systemd サービスなら: `sudo systemctl disable --now <service>` （停止前に影響調査）
- `secrets/gcs-key.json not found`
  - GCP連携が必須の環境（stg/prod）ではファイルを配置。devでは警告のみ

---

## プロジェクト構成（簡略）

- `app/frontend`: フロントエンド（Vite + React）
- `app/backend/*_api`: 各FastAPIサービス（ai/ledger/sql/rag）
- `app/nginx`: 逆プロキシ設定と証明書
- `config`: CSV/レポート等の設定群
- `dbdata`: PostgreSQLデータ永続化用ボリューム
- `docker-compose.yml`: 本番相当のベース設定
- `docker-compose.override.yml`: 開発用の上書き設定（ホットリロードなど）
- `makefile`: 起動/停止/再ビルドなどの補助

---

## 補足（開発の進め方）

- 日常操作は `make up|down|logs|rebuild ENV=dev` が基本
- 各サービスの詳細は `app/backend/*/README.md` や `frontend/README.md`（存在する場合）を参照
- 機密情報（APIキー・鍵ファイル・DBデータ）は必ず git 管理外（`.gitignore` 済）

---

## 環境分割 (dev / stg / prod) の仕組み

本リポジトリでは以下の方針で 3 環境を docker compose の override で切り替えます。

### ファイル構成

```
docker-compose.yml            # 共通土台 (サービス定義)
docker-compose.dev.yml        # dev 専用 (ホットリロード, ポート直接公開)
docker-compose.stg.yml        # stg 専用 (prod と同等, ポート 8080/8443)
docker-compose.prod.yml       # prod 専用 (nginx の 80/443 のみ公開)
env/
  ├─ .env.dev                 # 開発用環境変数 (ホットリロード前提)
  ├─ .env.stg                 # ステージング用 (本番に近い値)
  └─ .env.prod                # 本番用 (Secrets は別途 vault / 環境変数注入)
frontend/                     # React(TypeScript) SPA (Vite)
backend/                      # FastAPI (例: ai_api を backend として利用)
nginx/                        # リバースプロキシ (設定 / 証明書)
```

### サービス概要

| サービス | 役割 | dev | stg | prod |
|----------|------|-----|-----|------|
| frontend | React/Vite SPA | npm run dev (port 5173) | nginx runtime (内部) | nginx runtime (内部) |
| backend  | FastAPI | uvicorn --reload (port 8000) | 標準 uvicorn (内部) | 標準 uvicorn (内部) |
| nginx    | Reverse Proxy & Static | (未起動) | 8080/8443 公開 (COMPOSE_PROFILES=edge) | 80/443 公開 (COMPOSE_PROFILES=edge) |

### 起動例

```
make up                    # dev (ホットリロード, nginx 無し)
COMPOSE_PROFILES=edge make up ENV=stg   # stg (nginx 有効)
COMPOSE_PROFILES=edge make up ENV=prod  # prod (nginx 有効)
make logs ENV=dev S=ledger_api
COMPOSE_PROFILES=edge make rebuild ENV=stg
```

### なぜ override 方式か

- 共有設定 (依存関係 / ネットワーク / ビルド) を `docker-compose.yml` に集約し重複を削減
- 環境差分 (ポート公開 / コマンド / ボリュームマウント) のみ小さい override に記述
- 将来サービス追加時は共通に 1 箇所追加 + dev 用マウント追記のみで済む

### 初心者向けメモ

1. dev 環境ではコードを編集すると即座に反映されます (Vite + uvicorn --reload)
2. stg/prod ではコンテナ内にビルド成果物のみ含み、ホットリロードは無効です
3. stg/prod で nginx を動かすには `COMPOSE_PROFILES=edge` を付与 (付けない場合は内部検証用として API 群のみ起動)
4. 本番では `frontend` ビルド成果物は nginx イメージ内に含まれ、`frontend` 開発用コンテナは起動しません
4. 秘密情報(APIキー等)は `.env.prod` に直書きせず安全な仕組み(Secrets Manager, 環境変数注入)を利用してください

---

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
docker build -t local/sanbou-frontend:dev -f app/frontend/Dockerfile app/frontend
docker build -t local/sanbou-ai-api:dev -f app/backend/ai_api/Dockerfile app/backend/ai_api
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
docker build -t local/sanbou-ai-api:rollback -f app/backend/ai_api/Dockerfile.prev app/backend/ai_api
```
(
旧 Dockerfile を `Dockerfile.prev` として保管している想定。無い場合は Git 履歴から復元)

### 今後の追加改善候補

- Slim LibreOffice / unoconv 代替の検証 (ledger_api サイズさらなる削減)
- `requirements.txt` を `pip-tools` で lock 化
- マルチプラットフォーム (linux/amd64, arm64) ビルド対応
- Trivy / Grype を用いた CI の脆弱性スキャン

---

## GitHub Environments の Secrets を一括登録する

`.env.common` をリポジトリに含めず、GitHub Environments の Secrets に分離して管理するためのツールを用意しています。

前提
- GitHub CLI `gh` がインストール・ログイン済み（dry-run は未インストールでも可）
- JSON 形式の import の場合は `jq` が必要
- リポジトリ管理者権限（環境作成・Secrets登録）

スクリプト
- `scripts/gh_env_secrets_sync.sh`
  - .env / JSON / CSV から、dev / stg / prod などの環境に「同名キーで値だけ切替」を適用
  - 無い Environment は自動作成
  - `--dry-run` で差分確認のみ

使い方（例）
1) 単一環境に .env を取り込む（例: stg）
```bash
./scripts/gh_env_secrets_sync.sh \
  --repo <owner>/<repo> \
  --env stg \
  --file env/.env.common
```

2) 複数環境を JSON で一括
```bash
./scripts/gh_env_secrets_sync.sh \
  --repo <owner>/<repo> \
  --json scripts/examples/secrets.json
```

3) 複数環境を CSV で一括
```bash
./scripts/gh_env_secrets_sync.sh \
  --repo <owner>/<repo> \
  --csv scripts/examples/secrets.csv
```

オプション
- `--prefix APP_` ですべてのキーに接頭辞を付与
- `--dry-run` で実際の登録を行わずプレビュー

入力フォーマット
- .env: `KEY=VALUE` 形式（コメント・空行可）
- JSON（推奨）: `{ "dev": {"KEY":"VAL"}, "stg": {...}, "prod": {...} }`
- CSV: `env,key,value`（カンマを含む値は JSON の使用を推奨）

サンプル
- `scripts/examples/secrets.json`
- `scripts/examples/secrets.csv`
