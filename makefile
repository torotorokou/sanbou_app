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
## ★コンテナイメージの build & push（Artifact Registry）
##   - STG:  make publish-stg-images  STG_IMAGE_TAG=stg-YYYYMMDD
##   - PROD: make publish-prod-images PROD_IMAGE_TAG=prod-YYYYMMDD
##   - 事前に一度だけ: make gcloud-auth-docker
##
## ENV の意味（ざっくり）
##   - local_dev  : ローカル開発（ホットリロードあり・buildあり）
##   - local_demo : ローカルのデモ環境（dev とは別 compose）
##   - vm_stg     : GCP VM ステージング（VPN/Tailscale、Artifact Registry から pull）
##   - vm_prod    : GCP VM 本番（LB+IAP 経由、Artifact Registry から pull）
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
        backup restore-from-dump restore-from-sql

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
## Alembic（開発環境 local_dev 前提）
## ============================================================
.PHONY: al-rev al-rev-auto al-up al-down al-cur al-hist al-heads al-stamp \
        al-dump-schema-current al-init-from-schema

# Alembic は基本 local_dev で実行する想定
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
