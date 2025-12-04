## =============================================================
## Makefile (simple): dev / stg / prod / demo 用 docker compose ヘルパ
## -------------------------------------------------------------
## 主なターゲット:
##   make up        ENV=local_dev|local_stg|vm_stg|vm_prod|local_demo
##   make down      ENV=...
##   make logs      ENV=... S=ai_api
##   make rebuild   ENV=...
##   make health    ENV=...
##   make backup    ENV=local_dev
##   make restore-from-dump ENV=local_dev DUMP=backups/sanbou_dev_2025-12-03.dump
##   make restore-from-sql  ENV=local_demo SQL=backups/pg_all_2025-12-03.sql
##   make al-up / al-rev-auto / al-dump-schema-current / al-init-from-schema
## =============================================================

SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c

ENV ?= local_dev
ENV := $(strip $(ENV))
DC  := docker compose
BUILDKIT ?= 1
PROGRESS ?= plain

## =============================================================
## 環境マッピング (Environment Mapping)
## =============================================================
## ENV 値と対応する .env ファイル・docker-compose.yml の関係:
##
## ENV=local_dev  → docker/docker-compose.dev.yml
##                → env/.env.common + env/.env.local_dev + secrets/.env.local_dev.secrets
##                → ローカル開発環境（ホットリロード有効）
##
## ENV=local_demo → docker/docker-compose.local_demo.yml
##                → env/.env.common + env/.env.local_demo + secrets/.env.local_demo.secrets
##                → ローカルデモ環境（local_dev と完全分離）
##
## ENV=local_stg  → docker/docker-compose.stg.yml (STG_ENV_FILE=local_stg)
##                → env/.env.common + env/.env.local_stg + secrets/.env.local_stg.secrets
##                → ローカルSTG検証環境（本番近似構成、nginx 経由）
##
## ENV=vm_stg     → docker/docker-compose.stg.yml (STG_ENV_FILE=vm_stg)
##                → env/.env.common + env/.env.vm_stg + secrets/.env.vm_stg.secrets
##                → GCP VM ステージング環境
##
## ENV=vm_prod    → docker/docker-compose.prod.yml
##                → env/.env.common + env/.env.vm_prod + secrets/.env.vm_prod.secrets
##                → GCP VM 本番環境
##
## 注意: 環境変数スキーマの基準（Source of Truth）は env/.env.local_dev です
## =============================================================
ENV_CANON := $(ENV)

ifeq ($(ENV),dev)
	$(warning [compat] ENV=dev は非推奨。ENV=local_dev を使用してください)
	ENV_CANON := local_dev
endif
ifeq ($(ENV),stg)
	$(warning [compat] ENV=stg は非推奨。ENV=vm_stg を使用してください)
	ENV_CANON := vm_stg
endif
ifeq ($(ENV),prod)
	$(warning [compat] ENV=prod は非推奨。ENV=vm_prod を使用してください)
	ENV_CANON := vm_prod
endif

ENV_FILE_COMMON := env/.env.common
ENV_FILE        := env/.env.$(ENV)

ifeq ($(ENV_CANON),local_dev)
	ENV_FILE      := env/.env.local_dev
	COMPOSE_FILES := -f docker/docker-compose.dev.yml
	HEALTH_URL    := http://localhost:8001/health
else ifeq ($(ENV_CANON),local_stg)
	ENV_FILE      := env/.env.local_stg
	COMPOSE_FILES := -f docker/docker-compose.stg.yml
	HEALTH_PORT   := $(if $(STG_NGINX_HTTP_PORT),$(STG_NGINX_HTTP_PORT),8080)
	HEALTH_URL    := http://localhost:$(HEALTH_PORT)/health
	STG_ENV_FILE  := local_stg
else ifeq ($(ENV_CANON),vm_stg)
	ENV_FILE      := env/.env.vm_stg
	COMPOSE_FILES := -f docker/docker-compose.stg.yml
	HEALTH_URL    := http://stg.sanbou-app.jp/health
	STG_ENV_FILE  := vm_stg
else ifeq ($(ENV_CANON),vm_prod)
	ENV_FILE      := env/.env.vm_prod
	COMPOSE_FILES := -f docker/docker-compose.prod.yml
	HEALTH_URL    := https://sanbou-app.jp/health
else ifeq ($(ENV_CANON),local_demo)
	ENV_FILE      := env/.env.local_demo
	COMPOSE_FILES := -f docker/docker-compose.local_demo.yml
	# demo の health は core_api を想定（必要に応じて変更）
	HEALTH_URL    := http://localhost:8013/health
else
	$(error Unsupported ENV: $(ENV))
endif

SECRETS_FILE      := secrets/.env.$(ENV).secrets
# secrets ファイルは存在する場合のみ --env-file に載せる
COMPOSE_ENV_ARGS  := --env-file $(ENV_FILE_COMMON) --env-file $(ENV_FILE) \
                     $(if $(wildcard $(SECRETS_FILE)),--env-file $(SECRETS_FILE),)
DC_ENV_PREFIX     := $(if $(STG_ENV_FILE),STG_ENV_FILE=$(STG_ENV_FILE) ,)
COMPOSE_FILE_LIST := $(strip $(subst -f ,,$(COMPOSE_FILES)))
DC_FULL           := $(DC_ENV_PREFIX)$(DC) $(COMPOSE_ENV_ARGS) -p $(ENV) $(COMPOSE_FILES)

.PHONY: check up down logs ps restart rebuild health config \
        backup restore-from-dump restore-from-sql

## =============================================================
## 基本操作
## =============================================================
check:
	@for f in $(COMPOSE_FILE_LIST); do \
	  if [ ! -f "$$f" ]; then echo "[error] compose file $$f not found"; exit 1; fi; \
	done
	@if [ ! -f "$(ENV_FILE_COMMON)" ]; then echo "[error] $(ENV_FILE_COMMON) not found"; exit 1; fi
	@if [ ! -f "$(ENV_FILE)" ]; then echo "[error] $(ENV_FILE) not found"; exit 1; fi

up: check
	@echo "[info] UP (ENV=$(ENV))"
	DOCKER_BUILDKIT=$(BUILDKIT) BUILDKIT_PROGRESS=$(PROGRESS) \
	$(DC_FULL) up -d --build --remove-orphans
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

## =============================================================
## バックアップ / リストア（よく使う最小構成）
## =============================================================
DATE        := $(shell date +%F_%H%M%S)
BACKUP_DIR  ?= backups
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
	  pg_restore -U $(PGUSER) -d $(PGDB) /tmp/restore.dump \
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

## =============================================================
## Alembic（開発環境 local_dev 前提）
## =============================================================
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

## =============================================================
## Alembic: Schema Dump & Init (local_dev 前提)
## =============================================================
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
