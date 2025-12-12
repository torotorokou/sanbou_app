## =============================================================
## Makefile : dev / stg / prod / demo 用 docker compose ヘルパ
## -------------------------------------------------------------
## ★よく使うターゲット
##   - make up        ENV=local_dev|vm_stg|vm_prod|local_demo
##   - make down      ENV=...
##   - make rebuild   ENV=...
##   - make logs      ENV=... S=ai_api
##   - make health    ENV=...
##   - make backup    ENV=local_dev
##   - make restore-from-dump ENV=local_dev DUMP=backups/xxx.dump
##   - make restore-from-sql  ENV=local_demo SQL=backups/xxx.sql
##
## ★開発環境：nginx 付き起動（本番に近い構成）
##   - make dev-with-nginx    # nginx 経由で http://localhost:8080
##
## ★コンテナイメージの build & push(Artifact Registry)
##   - STG:  make publish-stg-images  STG_IMAGE_TAG=stg-YYYYMMDD
##   - PROD: make publish-prod-images PROD_IMAGE_TAG=prod-YYYYMMDD
##   - 事前に一度だけ: make gcloud-auth-docker
##
## ★STG → PROD へのイメージ昇格（別プロジェクト間コピー）
##   - make promote-stg-to-prod PROMOTE_SRC_TAG=stg-YYYYMMDD PROMOTE_DST_TAG=prod-YYYYMMDD
##     ※ STG_PROJECT_ID の Artifact Registry から PROD_PROJECT_ID へ docker pull/tag/push でコピー
##
## ★STG/PROD デプロイフロー
##   【STG】
##   1) ローカル: make publish-stg-images STG_IMAGE_TAG=stg-20251209
##   2) env/.env.vm_stg の IMAGE_TAG=stg-20251209 に更新
##   3) vm_stg で: make up ENV=vm_stg
##   【PROD】
##   1) ローカル: make publish-prod-images PROD_IMAGE_TAG=prod-20251209
##   2) env/.env.vm_prod の IMAGE_TAG=prod-20251209 に更新
##   3) vm_prod で: make up ENV=vm_prod
##
## ENV の意味(ざっくり)
##   - local_dev  : ローカル開発(ホットリロードあり・buildあり)
##   - local_demo : ローカルのデモ環境(dev とは別 compose)
##   - vm_stg     : GCP VM ステージング(VPN/Tailscale、Artifact Registry から pull)
##   - vm_prod    : GCP VM 本番(LB+IAP 経由、Artifact Registry から pull)
##
## -------------------------------------------------------------
## ★DB Bootstrap（ロール・権限の冪等セットアップ）
##   - app_readonly ロールと基本権限を冪等的にセットアップします
##   - Alembic マイグレーション前に必要（al-up/al-up-env は自動実行）
##   - 手動実行する場合:
##       make db-bootstrap-roles-env ENV=local_dev
##       make db-bootstrap-roles-env ENV=vm_stg
##       make db-bootstrap-roles-env ENV=vm_prod
##   - 冪等なので何度実行しても安全です
##
## -------------------------------------------------------------
## ★Alembic（DBマイグレーション）適用の考え方
##   - 既存ターゲット(al-up/al-cur等)は「local_dev固定」で動きます（従来通り）
##   - 追加ターゲット(al-up-env 等)は「ENV に追従」して適用できます:
##       make al-up-env  ENV=vm_stg
##       make al-cur-env ENV=vm_stg
##       make al-up-env  ENV=vm_prod
##   - al-up/al-up-env 実行時は自動的に db-bootstrap-roles-env が先に実行されます
##   - 注意:
##       * 対象ENVは先に `make up ENV=...` で起動しておくこと
##       * core_api コンテナ内で alembic を実行するため、
##         “migrationsファイルが含まれるイメージ” に更新されていること
## ============================================================


## ============================================================
## VM 上での暫定運用ルール(vm_stg / vm_prod)
## ------------------------------------------------------------
## ★ 重要: この VM では、vm_stg と vm_prod を「同時には起動しない」前提です
##   - 80番ポートはどちらの compose でも "80:80" を使うため、
##     必ず片方を down してからもう片方を up すること
##
## 例:
##   # STG を試すとき
##   make down ENV=vm_prod
##   make up   ENV=vm_stg
##
##   # PROD を試すとき
##   make down ENV=vm_stg
##   make up   ENV=vm_prod
##
## ★ nginx 動作確認(vm_stg / vm_prod 共通):
##   VM 内で:
##     curl -I http://localhost/health    # → HTTP/1.1 200 OK
##     curl -I http://localhost/          # → HTTP/1.1 200 OK, text/html
##                                        #    ※ Location: https://... が含まれないこと
##   Tailscale 経由:
##     http://<tailscale IP>/             # → React 画面が表示される
## ============================================================

SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c

## -------------------------------------------------------------
## グローバル環境変数
## -------------------------------------------------------------
ENV ?= local_dev
ENV := $(strip $(ENV))
DC  := docker compose
BUILDKIT ?= 1
PROGRESS ?= plain

## ============================================================
## 環境マッピング (Environment Mapping)
##   - ENV に応じて:
##     - 使用する docker-compose.yml
##     - 使用する .env ファイル
##     - health check URL
##     - build 有無
##
## ★ nginx 動作確認（HTTP リダイレクト修正後の確認手順）:
##
##   【vm_stg での確認】
##   VM 内で:
##     curl -I http://localhost/health    # → HTTP/1.1 200 OK
##     curl -I http://localhost/          # → HTTP/1.1 200 OK, Content-Type: text/html
##                                        #    ※ Location: https://... が含まれないこと
##   ローカル PC から (Tailscale 経由):
##     http://100.119.243.45/             # → React 画面が表示され、https へのリダイレクトなし
##
##   【vm_prod での確認】
##   VM 内で:
##     curl -I http://localhost/health    # → HTTP/1.1 200 OK
##     curl -I http://localhost/          # → HTTP/1.1 200 OK, Content-Type: text/html
##                                        #    ※ Location: https://localhost/ が含まれないこと
##   GCP LB + IAP 経由:
##     https://sanbou-app.jp/             # → React 画面が表示されること
##                                        #    ※ HTTPS は LB 側で終端、VM は HTTP(80) のみ
## ============================================================
ENV_CANON := $(ENV)

# 後方互換性のための警告と自動変換
ifeq ($(ENV),dev)
	$(warning [compat] ENV=dev は非推奨です。ENV=local_dev を使用してください)
	ENV_CANON := local_dev
endif
ifeq ($(ENV),stg)
	$(warning [compat] ENV=stg は非推奨です。ENV=vm_stg を使用してください)
	ENV_CANON := vm_stg
endif
ifeq ($(ENV),prod)
	$(warning [compat] ENV=prod は非推奨です。ENV=vm_prod を使用してください)
	ENV_CANON := vm_prod
endif
# local_stg / local_prod は廃止済み
ifeq ($(ENV),local_stg)
	$(error ENV=local_stg は廃止されました。ENV=vm_stg を使用してください)
endif
ifeq ($(ENV),local_prod)
	$(error ENV=local_prod は廃止されました。ENV=vm_prod を使用してください)
endif

# 共通 .env は常にこれ
ENV_FILE_COMMON := env/.env.common
# ENV 個別（後で ENV_CANON によって上書き）
ENV_FILE        := env/.env.$(ENV)

# ENV ごとの compose / env / health
ifeq ($(ENV_CANON),local_dev)
	ENV_FILE      := env/.env.local_dev
	COMPOSE_FILES := -f docker/docker-compose.dev.yml
	HEALTH_URL    := http://localhost:8001/health
else ifeq ($(ENV_CANON),vm_stg)
	ENV_FILE      := env/.env.vm_stg
	COMPOSE_FILES := -f docker/docker-compose.stg.yml
	HEALTH_URL    := http://100.64.0.1/health
else ifeq ($(ENV_CANON),vm_prod)
	ENV_FILE      := env/.env.vm_prod
	COMPOSE_FILES := -f docker/docker-compose.prod.yml
	HEALTH_URL    := https://sanbou-app.jp/health
else ifeq ($(ENV_CANON),local_demo)
	ENV_FILE      := env/.env.local_demo
	COMPOSE_FILES := -f docker/docker-compose.local_demo.yml
	HEALTH_URL    := http://localhost:8013/health
else
	$(error Unsupported ENV: $(ENV). Supported: local_dev, vm_stg, vm_prod, local_demo)
endif

# vm_stg / vm_prod は Artifact Registry からイメージ pull のみ (--build なし)
ifeq ($(ENV_CANON),vm_stg)
	UP_BUILD_FLAGS :=
else ifeq ($(ENV_CANON),vm_prod)
	UP_BUILD_FLAGS :=
else
	UP_BUILD_FLAGS := --build
endif

SECRETS_FILE      := secrets/.env.$(ENV).secrets
# secrets ファイルは存在する場合のみ --env-file に載せる
COMPOSE_ENV_ARGS  := --env-file $(ENV_FILE_COMMON) --env-file $(ENV_FILE) \
                     $(if $(wildcard $(SECRETS_FILE)),--env-file $(SECRETS_FILE),)
COMPOSE_FILE_LIST := $(strip $(subst -f ,,$(COMPOSE_FILES)))
DC_FULL           := $(DC) $(COMPOSE_ENV_ARGS) -p $(ENV) $(COMPOSE_FILES)

.PHONY: check up down logs ps restart rebuild health config \
        backup restore-from-dump restore-from-sql dev-with-nginx

## ============================================================
## 基本操作 (docker compose up / down など)
## ============================================================
check:
	@for f in $(COMPOSE_FILE_LIST); do \
	  if [ ! -f "$$f" ]; then echo "[error] compose file $$f not found"; exit 1; fi; \
	done
	@if [ ! -f "$(ENV_FILE_COMMON)" ]; then echo "[error] $(ENV_FILE_COMMON) not found"; exit 1; fi
	@if [ ! -f "$(ENV_FILE)" ]; then echo "[error] $(ENV_FILE) not found"; exit 1; fi

up: check
	@echo "[info] UP (ENV=$(ENV))"
	@echo "[debug] ENV=$(ENV) ENV_CANON=$(ENV_CANON)"
	@echo "[debug] COMPOSE_FILES=$(COMPOSE_FILES)"
	@echo "[debug] ENV_FILE=$(ENV_FILE)"
	@echo "[debug] COMPOSE_ENV_ARGS=$(COMPOSE_ENV_ARGS)"
	@echo "[debug] UP_BUILD_FLAGS=$(UP_BUILD_FLAGS)"
	@echo "[debug] DC_FULL=$(DC_FULL)"
	DOCKER_BUILDKIT=$(BUILDKIT) BUILDKIT_PROGRESS=$(PROGRESS) \
	$(DC_FULL) up -d $(UP_BUILD_FLAGS) --remove-orphans
	@echo "[ok] up done"

down:
	@echo "[info] DOWN (ENV=$(ENV))"
	@CIDS="$$( $(DC) -p $(ENV) ps -q | wc -l )"; \
	if [ "$$CIDS" -gt 0 ]; then \
	  $(DC) -p $(ENV) down --remove-orphans; \
	else echo "[info] no running containers"; fi

logs:
	$(DC) -p $(ENV) logs -f $(S)

ps:
	$(DC) -p $(ENV) ps

restart:
	$(MAKE) down ENV=$(ENV)
	$(MAKE) up   ENV=$(ENV)

PULL ?= 0
BUILD_PULL_FLAG := $(if $(filter 1,$(PULL)),--pull,)
NO_CACHE ?= 0
BUILD_NO_CACHE_FLAG := $(if $(filter 1,$(NO_CACHE)),--no-cache,)

rebuild: check
	@echo "[info] rebuild ENV=$(ENV)"
	$(MAKE) down ENV=$(ENV)
	DOCKER_BUILDKIT=$(BUILDKIT) BUILDKIT_PROGRESS=$(PROGRESS) \
	$(DC_FULL) build $(BUILD_PULL_FLAG) --no-cache
	DOCKER_BUILDKIT=$(BUILDKIT) BUILDKIT_PROGRESS=$(PROGRESS) \
	$(DC_FULL) up -d --remove-orphans
	@echo "[ok] rebuild done"

health:
	@echo "[info] health check -> $(HEALTH_URL)"
	@curl -I "$(HEALTH_URL)" || echo "[warn] curl failed"

config: check
	$(DC_FULL) config

## ============================================================
## 開発環境：nginx 付き起動 (本番に近い構成での開発・検証)
## ============================================================
## 使い方:
##   make dev-with-nginx        # nginx 付きで起動
##   make down ENV=local_dev    # 停止
##
## アクセス:
##   http://localhost:8080      # nginx 経由 (本番と同様のルーティング)
##   http://localhost:5173      # フロントエンド直接
##   http://localhost:8001      # ai_api 直接
##   http://localhost:8002      # core_api 直接
## ============================================================
dev-with-nginx:
	@echo "[info] Starting local_dev with nginx (profile: with-nginx)"
	@echo "[info] Access via: http://localhost:8080 (nginx)"
	DOCKER_BUILDKIT=$(BUILDKIT) BUILDKIT_PROGRESS=$(PROGRESS) \
	docker compose -f docker/docker-compose.dev.yml -p local_dev \
	  --env-file env/.env.common --env-file env/.env.local_dev \
	  $(if $(wildcard secrets/.env.local_dev.secrets),--env-file secrets/.env.local_dev.secrets,) \
	  --profile with-nginx up -d --build --remove-orphans
	@echo "[ok] Dev environment with nginx started"
	@echo "[info] Check health: curl http://localhost:8080/health"

## ============================================================
## バックアップ / リストア（よく使う最小構成）
## ============================================================
DATE        := $(shell date +%F_%H%M%S)
BACKUP_DIR  ?= /mnt/c/Users/synth/Desktop/backups
PG_SERVICE  ?= db
PGUSER      ?= myuser
# デフォルト: sanbou_dev（必要に応じて PGDB=... で上書き）
PGDB        ?= sanbou_dev

backup:
	@echo "[info] logical backup (pg_dump) ENV=$(ENV)"
	@mkdir -p "$(BACKUP_DIR)"
	$(DC_FULL) exec -T $(PG_SERVICE) pg_dump -U $(PGUSER) -d $(PGDB) \
	  --format=custom --file=/tmp/$(PGDB).dump
	$(DC_FULL) cp $(PG_SERVICE):/tmp/$(PGDB).dump \
	  "$(BACKUP_DIR)/$(PGDB)_$(ENV)_$(DATE).dump"
	@$(DC_FULL) exec -T $(PG_SERVICE) rm -f /tmp/$(PGDB).dump || true
	@echo "[ok] backup -> $(BACKUP_DIR)/$(PGDB)_$(ENV)_$(DATE).dump"

.PHONY: restore-from-dump
DUMP ?= backups/sanbou_dev_2025-12-03.dump

restore-from-dump: check
	@if [ ! -f "$(DUMP)" ]; then \
	  echo "[error] dump file not found: $(DUMP)"; exit 1; \
	fi
	@echo "[info] Restoring $(DUMP) into DB=$(PGDB) (ENV=$(ENV))"
	$(DC_FULL) cp "$(DUMP)" $(PG_SERVICE):/tmp/restore.dump
	$(DC_FULL) exec -T $(PG_SERVICE) bash -lc '\
	  dropdb  -U $(PGUSER) --if-exists --force $(PGDB) && \
	  createdb -U $(PGUSER) $(PGDB) && \
	  pg_restore -U $(PGUSER) -d $(PGDB) --no-owner --no-acl /tmp/restore.dump \
	'
	@$(DC_FULL) exec -T $(PG_SERVICE) rm -f /tmp/restore.dump || true
	@echo "[ok] restore-from-dump completed"

## -------------------------------------------------------------
## SQL ファイル（.sql）からのリストア（別環境への適用など）
##   使い方:
##     make restore-from-sql ENV=local_demo \
##          SQL=backups/pg_all_2025-12-03.sql
## -------------------------------------------------------------
.PHONY: restore-from-sql
SQL ?=

restore-from-sql: check
	@if [ -z "$(SQL)" ]; then \
	  echo "[error] SQL parameter is required."; \
	  echo "Usage: make restore-from-sql ENV=$(ENV) SQL=backups/xxx.sql"; \
	  exit 1; \
	fi
	@if [ ! -f "$(SQL)" ]; then \
	  echo "[error] SQL file not found: $(SQL)"; exit 1; \
	fi
	@echo "[info] Restoring SQL $(SQL) into DB=$(PGDB) (ENV=$(ENV))"
	@cat "$(SQL)" | $(DC_FULL) exec -T $(PG_SERVICE) \
	  psql -U $(PGUSER) -d $(PGDB)
	@echo "[ok] restore-from-sql completed"

## ============================================================
## DB Bootstrap: Roles & Permissions (冪等セットアップ)
## ============================================================
## 目的:
##   - app_readonly ロールと基本権限を冪等的にセットアップ
##   - Alembic マイグレーション実行前に毎回実行可能（冪等なので安全）
##
## 使い方:
##   make db-bootstrap-roles-env ENV=local_dev
##   make db-bootstrap-roles-env ENV=vm_stg
##   make db-bootstrap-roles-env ENV=vm_prod
##
## 注意:
##   - 対象ENVは先に `make up ENV=...` で起動しておくこと
##   - VM上で実行する場合、DBコンテナ内の環境変数を使用するため
##     ホスト側の環境変数には依存しない
## ============================================================
.PHONY: db-bootstrap-roles-env

BOOTSTRAP_ROLES_SQL ?= scripts/db/bootstrap_roles.sql

db-bootstrap-roles-env: check
	@echo "[info] Bootstrap DB roles and permissions (ENV=$(ENV))"
	@if [ ! -f "$(BOOTSTRAP_ROLES_SQL)" ]; then \
	  echo "[error] $(BOOTSTRAP_ROLES_SQL) not found"; exit 1; \
	fi
	@echo "[info] Copying SQL to container..."
	$(DC_FULL) cp $(BOOTSTRAP_ROLES_SQL) $(PG_SERVICE):/tmp/bootstrap_roles.sql
	@echo "[info] Executing bootstrap SQL..."
	$(DC_FULL) exec -T $(PG_SERVICE) sh -c '\
	  psql -U "$$POSTGRES_USER" -d "$${POSTGRES_DB:-postgres}" \
	       -v ON_ERROR_STOP=0 \
	       -f /tmp/bootstrap_roles.sql'
	@echo "[info] Cleaning up temporary file..."
	-$(DC_FULL) exec -T $(PG_SERVICE) rm -f /tmp/bootstrap_roles.sql
	@echo "[ok] db-bootstrap-roles-env completed"

## ============================================================
## Alembic（開発環境 local_dev 前提）
## ============================================================
.PHONY: al-rev al-rev-auto al-up al-down al-cur al-hist al-heads al-stamp \
        al-dump-schema-current al-init-from-schema \
        al-up-env al-down-env al-cur-env al-hist-env al-heads-env al-stamp-env

# Alembic は基本 local_dev で実行する想定（従来どおり固定）
ALEMBIC_DC := docker compose -f docker/docker-compose.dev.yml -p local_dev
ALEMBIC    := $(ALEMBIC_DC) exec core_api alembic -c /backend/migrations/alembic.ini

MSG    ?= update schema
REV_ID ?= $(shell date +%Y%m%d_%H%M%S%3N)  # 例: 20251104_153045123

al-rev:
	@echo "[al-rev] REV_ID=$(REV_ID) MSG=$(MSG)"
	$(ALEMBIC) revision -m "$(MSG)" --rev-id $(REV_ID)

al-rev-auto:
	@echo "[al-rev-auto] REV_ID=$(REV_ID) MSG=$(MSG)"
	$(ALEMBIC) revision --autogenerate -m "$(MSG)" --rev-id $(REV_ID)

al-up:
	@echo "[info] Running DB bootstrap before Alembic migration (local_dev)..."
	@$(MAKE) db-bootstrap-roles-env ENV=local_dev
	@echo "[info] Starting Alembic migration..."
	$(ALEMBIC) upgrade head

al-down:
	$(ALEMBIC) downgrade -1

al-cur:
	$(ALEMBIC) current

al-hist:
	$(ALEMBIC) history

al-heads:
	$(ALEMBIC) heads

# 既存 DB に「適用済み印」を付ける
# 使い方: make al-stamp REV=20251104_153045123
al-stamp:
	$(ALEMBIC) stamp $(REV)

## ------------------------------------------------------------
## Alembic（ENVに追従して適用する版：vm_stg / vm_prod でも使える）
## 使い方:
##   make al-cur-env ENV=vm_stg
##   make al-up-env  ENV=vm_stg
##   make al-up-env  ENV=vm_prod
## ------------------------------------------------------------
ALEMBIC_INI ?= /backend/migrations/alembic.ini
ALEMBIC_ENV := $(DC_FULL) exec core_api alembic -c $(ALEMBIC_INI)

al-up-env: check
	@echo "[info] Running DB bootstrap before Alembic migration..."
	@$(MAKE) db-bootstrap-roles-env ENV=$(ENV)
	@echo "[info] Starting Alembic migration..."
	$(ALEMBIC_ENV) upgrade head

al-down-env: check
	$(ALEMBIC_ENV) downgrade -1

al-cur-env: check
	$(ALEMBIC_ENV) current

al-hist-env: check
	$(ALEMBIC_ENV) history

al-heads-env: check
	$(ALEMBIC_ENV) heads

# 既存 DB に「適用済み印」を付ける（ENV追従）
# 使い方: make al-stamp-env ENV=vm_prod REV=<HEAD_REVISION>
al-stamp-env: check
	$(ALEMBIC_ENV) stamp $(REV)

## ============================================================
## Alembic: Schema Dump & Init (local_dev 前提)
## ============================================================
al-dump-schema-current:
	@echo "[info] Dumping current schema to sql_current/schema_head.sql"
	@bash scripts/db/dump_schema_current.sh

al-init-from-schema:
	@echo "[info] Initializing database from schema_head.sql (local_dev)"
	@if [ ! -f app/backend/core_api/migrations/alembic/sql_current/schema_head.sql ]; then \
	  echo "[error] schema_head.sql not found. Run 'make al-dump-schema-current' first."; \
	  exit 1; \
	fi
	docker compose -f docker/docker-compose.dev.yml -p local_dev \
	  exec -T db psql -U myuser -d sanbou_dev \
	  < app/backend/core_api/migrations/alembic/sql_current/schema_head.sql
	@echo "[ok] Schema initialized. Now run: make al-stamp REV=<HEAD_REVISION>"

## ============================================================
## Artifact Registry 設定 (STG / PROD 共通)
##   - ローカルPCで build / push するための設定
##   - STG: --target stg でビルド
##   - PROD: --target prod でビルド
## ============================================================

# STG 設定
STG_REGION         ?= asia-northeast1
STG_PROJECT_ID     ?= honest-sanbou-app-stg
STG_ARTIFACT_REPO  ?= sanbou-app
STG_IMAGE_REGISTRY := $(STG_REGION)-docker.pkg.dev/$(STG_PROJECT_ID)/$(STG_ARTIFACT_REPO)
STG_IMAGE_TAG      ?= stg-latest
# 後方互換: 昔のドキュメントで IMAGE_TAG を使っている場合に対応（STG 側）
ifdef IMAGE_TAG
  STG_IMAGE_TAG := $(IMAGE_TAG)
endif

# PROD 設定
PROD_REGION         ?= asia-northeast1
PROD_PROJECT_ID     ?= honest-sanbou-app-prod
PROD_ARTIFACT_REPO  ?= sanbou-app
PROD_IMAGE_REGISTRY := $(PROD_REGION)-docker.pkg.dev/$(PROD_PROJECT_ID)/$(PROD_ARTIFACT_REPO)
PROD_IMAGE_TAG      ?= prod-latest
# 後方互換: IMAGE_TAG を指定したら PROD 側にも反映（必要に応じて使う）
ifdef IMAGE_TAG
  PROD_IMAGE_TAG := $(IMAGE_TAG)
endif

## STG → PROD 昇格用タグ（デフォルトは stg-latest → prod-latest）
PROMOTE_SRC_TAG ?= stg-latest
PROMOTE_DST_TAG ?= prod-latest

## ------------------------------------------------------------
## gcloud 認証（STG / PROD 共通）
##   - 一度だけ実行しておけば OK
##   - gcloud auth login / config set project は事前に実施しておくこと
## ------------------------------------------------------------
.PHONY: gcloud-auth-docker
gcloud-auth-docker:
	@gcloud auth configure-docker $(STG_REGION)-docker.pkg.dev
	@gcloud auth configure-docker $(PROD_REGION)-docker.pkg.dev

## ============================================================
## STG 用 Docker イメージ build & push
##  - ローカルPCで実行する前提
##  - VM (vm_stg) では build せず pull + up だけ
##  - 使い方:
##      make publish-stg-images STG_IMAGE_TAG=stg-20251208
##      NO_CACHE=1 PULL=1 make publish-stg-images STG_IMAGE_TAG=stg-20251208
## ============================================================
.PHONY: build-stg-images push-stg-images publish-stg-images

build-stg-images:
	@echo ">>> Build STG images (tag=$(STG_IMAGE_TAG), target=stg)"
	docker build $(BUILD_PULL_FLAG) $(BUILD_NO_CACHE_FLAG) \
	  -t $(STG_IMAGE_REGISTRY)/core_api:$(STG_IMAGE_TAG) \
	  -f app/backend/core_api/Dockerfile --target stg app/backend
	docker build $(BUILD_PULL_FLAG) $(BUILD_NO_CACHE_FLAG) \
	  -t $(STG_IMAGE_REGISTRY)/plan_worker:$(STG_IMAGE_TAG) \
	  -f app/backend/plan_worker/Dockerfile --target stg app/backend
	docker build $(BUILD_PULL_FLAG) $(BUILD_NO_CACHE_FLAG) \
	  -t $(STG_IMAGE_REGISTRY)/ai_api:$(STG_IMAGE_TAG) \
	  -f app/backend/ai_api/Dockerfile --target stg app/backend
	docker build $(BUILD_PULL_FLAG) $(BUILD_NO_CACHE_FLAG) \
	  -t $(STG_IMAGE_REGISTRY)/ledger_api:$(STG_IMAGE_TAG) \
	  -f app/backend/ledger_api/Dockerfile --target stg app/backend
	docker build $(BUILD_PULL_FLAG) $(BUILD_NO_CACHE_FLAG) \
	  -t $(STG_IMAGE_REGISTRY)/rag_api:$(STG_IMAGE_TAG) \
	  -f app/backend/rag_api/Dockerfile --target stg app/backend
	docker build $(BUILD_PULL_FLAG) $(BUILD_NO_CACHE_FLAG) \
	  -t $(STG_IMAGE_REGISTRY)/manual_api:$(STG_IMAGE_TAG) \
	  -f app/backend/manual_api/Dockerfile --target stg app/backend
	docker build $(BUILD_PULL_FLAG) $(BUILD_NO_CACHE_FLAG) \
	  -t $(STG_IMAGE_REGISTRY)/nginx:$(STG_IMAGE_TAG) \
	  -f app/frontend/Dockerfile --target stg app/frontend

push-stg-images:
	@echo ">>> Push STG images (tag=$(STG_IMAGE_TAG))"
	@for svc in core_api plan_worker ai_api ledger_api rag_api manual_api nginx; do \
	  echo "  -> push $(STG_IMAGE_REGISTRY)/$$svc:$(STG_IMAGE_TAG)"; \
	  docker push $(STG_IMAGE_REGISTRY)/$$svc:$(STG_IMAGE_TAG); \
	done

publish-stg-images: build-stg-images push-stg-images
	@echo "[ok] STG images built & pushed (tag=$(STG_IMAGE_TAG))"

## ============================================================
## PROD 用 Docker イメージ build & push
##  - ローカルPCで実行する前提
##  - VM (vm_prod) では build せず pull + up だけ
##  - 使い方:
##      make publish-prod-images PROD_IMAGE_TAG=prod-20251209
##      NO_CACHE=1 PULL=1 make publish-prod-images PROD_IMAGE_TAG=prod-20251209
## ============================================================
.PHONY: build-prod-images push-prod-images publish-prod-images

build-prod-images:
	@echo ">>> Build PROD images (tag=$(PROD_IMAGE_TAG), target=prod)"
	docker build $(BUILD_PULL_FLAG) $(BUILD_NO_CACHE_FLAG) \
	  -t $(PROD_IMAGE_REGISTRY)/core_api:$(PROD_IMAGE_TAG) \
	  -f app/backend/core_api/Dockerfile --target prod app/backend
	docker build $(BUILD_PULL_FLAG) $(BUILD_NO_CACHE_FLAG) \
	  -t $(PROD_IMAGE_REGISTRY)/plan_worker:$(PROD_IMAGE_TAG) \
	  -f app/backend/plan_worker/Dockerfile --target prod app/backend
	docker build $(BUILD_PULL_FLAG) $(BUILD_NO_CACHE_FLAG) \
	  -t $(PROD_IMAGE_REGISTRY)/ai_api:$(PROD_IMAGE_TAG) \
	  -f app/backend/ai_api/Dockerfile --target prod app/backend
	docker build $(BUILD_PULL_FLAG) $(BUILD_NO_CACHE_FLAG) \
	  -t $(PROD_IMAGE_REGISTRY)/ledger_api:$(PROD_IMAGE_TAG) \
	  -f app/backend/ledger_api/Dockerfile --target prod app/backend
	docker build $(BUILD_PULL_FLAG) $(BUILD_NO_CACHE_FLAG) \
	  -t $(PROD_IMAGE_REGISTRY)/rag_api:$(PROD_IMAGE_TAG) \
	  -f app/backend/rag_api/Dockerfile --target prod app/backend
	docker build $(BUILD_PULL_FLAG) $(BUILD_NO_CACHE_FLAG) \
	  -t $(PROD_IMAGE_REGISTRY)/manual_api:$(PROD_IMAGE_TAG) \
	  -f app/backend/manual_api/Dockerfile --target prod app/backend
	docker build $(BUILD_PULL_FLAG) $(BUILD_NO_CACHE_FLAG) \
	  -t $(PROD_IMAGE_REGISTRY)/nginx:$(PROD_IMAGE_TAG) \
	  -f app/frontend/Dockerfile --target prod app/frontend

push-prod-images:
	@echo ">>> Push PROD images (tag=$(PROD_IMAGE_TAG))"
	@for svc in core_api plan_worker ai_api ledger_api rag_api manual_api nginx; do \
	  echo "  -> push $(PROD_IMAGE_REGISTRY)/$$svc:$(PROD_IMAGE_TAG)"; \
	  docker push $(PROD_IMAGE_REGISTRY)/$$svc:$(PROD_IMAGE_TAG); \
	done

publish-prod-images: build-prod-images push-prod-images
	@echo "[ok] PROD images built & pushed (tag=$(PROD_IMAGE_TAG))"

## ============================================================
## STG → PROD イメージ昇格（別プロジェクト Artifact Registry コピー）
##   使い方:
##     make promote-stg-to-prod PROMOTE_SRC_TAG=stg-20251209 PROMOTE_DST_TAG=prod-20251209
##   実装:
##     docker pull (STG) → docker tag (PROD名) → docker push (PROD)
## ============================================================
.PHONY: promote-stg-to-prod

promote-stg-to-prod:
	@echo "[info] Promote images from STG to PROD (docker pull/tag/push)"
	@echo "[info]   STG:  $(STG_IMAGE_REGISTRY):$(PROMOTE_SRC_TAG)"
	@echo "[info]   PROD: $(PROD_IMAGE_REGISTRY):$(PROMOTE_DST_TAG)"
	@for svc in core_api plan_worker ai_api ledger_api rag_api manual_api nginx; do \
	  SRC_IMG="$(STG_IMAGE_REGISTRY)/$$svc:$(PROMOTE_SRC_TAG)"; \
	  DST_IMG="$(PROD_IMAGE_REGISTRY)/$$svc:$(PROMOTE_DST_TAG)"; \
	  echo "  -> copy $$svc: $(PROMOTE_SRC_TAG) -> $(PROMOTE_DST_TAG)"; \
	  echo "     SRC=$$SRC_IMG"; \
	  echo "     DST=$$DST_IMG"; \
	  docker pull $$SRC_IMG; \
	  docker tag  $$SRC_IMG $$DST_IMG; \
	  docker push $$DST_IMG; \
	done
	@echo "[ok] promoted STG tag '$(PROMOTE_SRC_TAG)' to PROD tag '$(PROMOTE_DST_TAG)' (via docker)"

## ============================================================
## イメージ存在確認（デバッグ用）
## ============================================================
.PHONY: check-stg-images check-prod-images

check-stg-images:
	@echo "[info] Checking STG images (tag=$(STG_IMAGE_TAG))"
	@for svc in core_api plan_worker ai_api ledger_api rag_api manual_api nginx; do \
	  echo "  -> checking $(STG_IMAGE_REGISTRY)/$$svc:$(STG_IMAGE_TAG)"; \
	  gcloud artifacts docker images list $(STG_REGION)-docker.pkg.dev/$(STG_PROJECT_ID)/$(STG_ARTIFACT_REPO) \
	    --filter="package=$$svc AND tags:$(STG_IMAGE_TAG)" --format="table(package,tags)" || true; \
	done

check-prod-images:
	@echo "[info] Checking PROD images (tag=$(PROD_IMAGE_TAG))"
	@for svc in core_api plan_worker ai_api ledger_api rag_api manual_api nginx; do \
	  echo "  -> checking $(PROD_IMAGE_REGISTRY)/$$svc:$(PROD_IMAGE_TAG)"; \
	  gcloud artifacts docker images list $(PROD_REGION)-docker.pkg.dev/$(PROD_PROJECT_ID)/$(PROD_ARTIFACT_REPO) \
	    --filter="package=$$svc AND tags:$(PROD_IMAGE_TAG)" --format="table(package,tags)" || true; \
	done

## ============================================================
## セキュリティスキャン（Trivy）
## ============================================================
.PHONY: scan-images scan-local-images install-trivy security-check \
        scan-stg-images scan-prod-images

# Trivy インストール確認・インストール
install-trivy:
	@echo "=== Checking Trivy installation ==="
	@if ! command -v trivy &> /dev/null; then \
	  echo "Trivy not found. Installing..."; \
	  if [ "$$(uname)" = "Darwin" ]; then \
	    brew install aquasecurity/trivy/trivy; \
	  elif [ "$$(uname)" = "Linux" ]; then \
	    wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -; \
	    echo "deb https://aquasecurity.github.io/trivy-repo/deb $$(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list; \
	    sudo apt-get update && sudo apt-get install trivy; \
	  else \
	    echo "Unsupported OS. Please install Trivy manually: https://aquasecurity.github.io/trivy/"; \
	    exit 1; \
	  fi; \
	else \
	  echo "✅ Trivy is already installed ($$(trivy --version))"; \
	fi

# ローカルビルド済みイメージをスキャン
scan-local-images: install-trivy
	@echo "=== Scanning local Docker images for vulnerabilities ==="
	@SERVICES="frontend core_api ai_api ledger_api rag_api manual_api plan_worker"; \
	for svc in $$SERVICES; do \
	  IMAGE_NAME="local_dev-$$svc"; \
	  if docker images | grep -q "$$IMAGE_NAME"; then \
	    echo ""; \
	    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	    echo "Scanning: $$IMAGE_NAME"; \
	    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	    trivy image --severity HIGH,CRITICAL --exit-code 0 $$IMAGE_NAME || true; \
	  else \
	    echo "⚠️  Image not found: $$IMAGE_NAME (skipping)"; \
	  fi; \
	done
	@echo ""
	@echo "✅ Scan completed. Review HIGH/CRITICAL vulnerabilities above."

# Artifact Registry のイメージをスキャン（STG）
scan-stg-images: install-trivy
	@echo "=== Scanning STG images in Artifact Registry ==="
	@SERVICES="core_api plan_worker ai_api ledger_api rag_api manual_api nginx"; \
	for svc in $$SERVICES; do \
	  IMAGE="$(STG_IMAGE_REGISTRY)/$$svc:$(STG_IMAGE_TAG)"; \
	  echo ""; \
	  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	  echo "Scanning: $$IMAGE"; \
	  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	  trivy image --severity HIGH,CRITICAL --exit-code 1 $$IMAGE || \
	    (echo "❌ Vulnerabilities found in $$IMAGE"; exit 1); \
	done
	@echo "✅ All STG images passed security scan"

# Artifact Registry のイメージをスキャン（PROD）
scan-prod-images: install-trivy
	@echo "=== Scanning PROD images in Artifact Registry ==="
	@SERVICES="core_api plan_worker ai_api ledger_api rag_api manual_api nginx"; \
	for svc in $$SERVICES; do \
	  IMAGE="$(PROD_IMAGE_REGISTRY)/$$svc:$(PROD_IMAGE_TAG)"; \
	  echo ""; \
	  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	  echo "Scanning: $$IMAGE"; \
	  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	  trivy image --severity HIGH,CRITICAL --exit-code 1 $$IMAGE || \
	    (echo "❌ Vulnerabilities found in $$IMAGE"; exit 1); \
	done
	@echo "✅ All PROD images passed security scan"

# エイリアス（デフォルトはローカルスキャン）
scan-images: scan-local-images

# CI/CD パイプライン用の総合セキュリティチェック
security-check: scan-local-images
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "✅ Security checks completed successfully"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
