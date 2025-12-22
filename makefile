## =============================================================
## Makefile : sanbou_app 全環境統合管理ツール
## =============================================================
##
## 📚 ドキュメント
##    MAKEFILE_QUICKREF.md           - クイックリファレンス
##    docs/infrastructure/MAKEFILE_GUIDE.md - 詳細ガイド
##
## 🚀 よく使うコマンド
##    make up ENV=local_dev          - 環境起動
##    make down ENV=local_dev        - 環境停止
##    make logs ENV=local_dev S=xxx  - ログ確認
##    make al-up-env ENV=local_dev   - DBマイグレーション（新規環境は自動でbaseline適用）
##    make backup ENV=local_dev      - バックアップ
##
## 🆕 新規環境構築（baseline→roles→alembic を自動実行）
##    make al-up-env ENV=vm_stg      - ステージング環境（初回でも自動で器作成）
##    make al-up-env ENV=vm_prod FORCE=1  - 本番環境（初回のみFORCE=1必須）
##
## 🌍 環境 (ENV)
##    local_dev  - ローカル開発（自動ビルド）
##    local_demo - ローカルデモ
##    vm_stg     - GCP VM ステージング（Artifact Registry）
##    vm_prod    - GCP VM 本番（Artifact Registry）
##
## ⚠️ VM環境での注意
##    - vm_stg と vm_prod は同時起動不可（ポート80競合）
##    - VM環境ではローカルでイメージビルド後 pull して使用
##    - 本番マイグレーション前に必ずバックアップ取得
##
## =============================================================

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
	backup restore-from-dump restore-from-sql dev-with-nginx pull

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
	@if [ "$(PULL)" = "1" ]; then \
		if [ "$(ENV_CANON)" = "vm_stg" ] || [ "$(ENV_CANON)" = "vm_prod" ]; then \
			echo "[info] PULL=1 and ENV_CANON=$(ENV_CANON) -> pulling images before up"; \
			$(DC_FULL) pull; \
		fi; \
	fi; \
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

## PULL: control whether to run `docker compose pull` before `up`
## Default depends on ENV_CANON (use ?= so user-specified value takes precedence)
ifeq ($(ENV_CANON),vm_stg)
PULL ?= 1
else ifeq ($(ENV_CANON),vm_prod)
PULL ?= 1
else
PULL ?= 0
endif
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

pull: check
	@echo "[info] Pulling images (ENV=$(ENV))"
	$(DC_FULL) pull

health:
	@echo "[info] health check -> $(HEALTH_URL)"
	@curl -I "$(HEALTH_URL)" || echo "[warn] curl failed"

config: check
	$(DC_FULL) config

## ============================================================
## Worker 管理（個別起動・停止・ログ確認）
## ============================================================
## 使い方:
##   make worker-up ENV=local_dev WORKER=inbound_forecast_worker
##   make worker-logs ENV=local_dev WORKER=inbound_forecast_worker
##   make worker-restart ENV=local_dev WORKER=inbound_forecast_worker
##   make worker-down ENV=local_dev WORKER=inbound_forecast_worker
## ============================================================
WORKER ?= inbound_forecast_worker

worker-up: check
	@echo "[info] Starting $(WORKER) in $(ENV_CANON)..."
	DOCKER_BUILDKIT=$(BUILDKIT) BUILDKIT_PROGRESS=$(PROGRESS) \
	$(DC_FULL) up -d $(UP_BUILD_FLAGS) $(WORKER)
	@echo "[ok] $(WORKER) started"

worker-down: check
	@echo "[info] Stopping $(WORKER) in $(ENV_CANON)..."
	$(DC_FULL) stop $(WORKER)
	$(DC_FULL) rm -f $(WORKER)
	@echo "[ok] $(WORKER) stopped"

worker-logs: check
	$(DC_FULL) logs -f --tail=100 $(WORKER)

worker-restart: check
	@echo "[info] Restarting $(WORKER) in $(ENV_CANON)..."
	$(DC_FULL) restart $(WORKER)
	@echo "[ok] $(WORKER) restarted"

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
## バックアップ / リストア（環境別自動対応）
## ============================================================
## 注意:
##   - POSTGRES_USER と POSTGRES_DB は各環境の .env ファイルから自動取得
##   - local_dev: myuser / sanbou_dev
##   - vm_stg: sanbou_app_stg / sanbou_stg
##   - vm_prod: sanbou_app_prod / sanbou_prod
## ============================================================
DATE        := $(shell date +%F_%H%M%S)
BACKUP_DIR  ?= /mnt/c/Users/synth/Desktop/backups
PG_SERVICE  ?= db

backup:
	@echo "[info] logical backup (pg_dump) ENV=$(ENV)"
	@mkdir -p "$(BACKUP_DIR)"
	$(DC_FULL) exec -T $(PG_SERVICE) sh -c '\
	  pg_dump -U "$$POSTGRES_USER" -d "$${POSTGRES_DB:-postgres}" \
	    --format=custom --file=/tmp/backup.dump'
	$(DC_FULL) cp $(PG_SERVICE):/tmp/backup.dump \
	  "$(BACKUP_DIR)/$(ENV)_$(DATE).dump"
	@$(DC_FULL) exec -T $(PG_SERVICE) rm -f /tmp/backup.dump || true
	@echo "[ok] backup -> $(BACKUP_DIR)/$(ENV)_$(DATE).dump"

.PHONY: restore-from-dump
DUMP ?= backups/sanbou_dev_2025-12-03.dump

restore-from-dump: check
	@if [ ! -f "$(DUMP)" ]; then \
	  echo "[error] dump file not found: $(DUMP)"; exit 1; \
	fi
	@echo "[info] Restoring $(DUMP) (ENV=$(ENV))"
	@echo "[info] Using container's POSTGRES_USER and POSTGRES_DB environment variables"
	$(DC_FULL) cp "$(DUMP)" $(PG_SERVICE):/tmp/restore.dump
	$(DC_FULL) exec -T $(PG_SERVICE) sh -c '\
	  dropdb  -U "$$POSTGRES_USER" --if-exists --force "$${POSTGRES_DB:-postgres}" && \
	  createdb -U "$$POSTGRES_USER" "$${POSTGRES_DB:-postgres}" && \
	  pg_restore -U "$$POSTGRES_USER" -d "$${POSTGRES_DB:-postgres}" --no-owner --no-acl /tmp/restore.dump \
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
	@echo "[info] Restoring SQL $(SQL) (ENV=$(ENV))"
	@echo "[info] Using container's POSTGRES_USER and POSTGRES_DB environment variables"
	@cat "$(SQL)" | $(DC_FULL) exec -T $(PG_SERVICE) sh -c '\
	  psql -U "$$POSTGRES_USER" -d "$${POSTGRES_DB:-postgres}"'
	@echo "[ok] restore-from-sql completed"

## ============================================================
## DB Baseline: スキーマ・テーブル構造の自動適用（冪等）
## ============================================================
## 目的:
##   - 新規環境で schema_baseline.sql を自動適用してスキーマ/テーブルを作成
##   - marker table (public.schema_baseline_meta) で適用済み判定
##   - vm_prod では誤適用防止のため FORCE=1 必須
##
## 使い方:
##   make db-ensure-baseline-env ENV=vm_stg
##   make db-ensure-baseline-env ENV=vm_prod FORCE=1
##
## 注意:
##   - 対象ENVは先に `make up ENV=...` で起動しておくこと
##   - schema_baseline.sql に alembic_version が含まれていたらエラー
##   - 中途半端な状態（stgだけ存在等）はボリューム削除推奨
## ============================================================
.PHONY: db-ensure-baseline-env

BASELINE_SQL := app/backend/core_api/migrations_v2/sql/schema_baseline.sql

db-ensure-baseline-env: check
	@echo "[info] Checking baseline status (ENV=$(ENV))"
	@if [ ! -f "$(BASELINE_SQL)" ]; then \
	  echo "[error] $(BASELINE_SQL) not found"; exit 1; \
	fi
	@if grep -q "alembic_version" "$(BASELINE_SQL)"; then \
	  echo "[error] $(BASELINE_SQL) contains 'alembic_version' - this must be removed!"; exit 1; \
	fi
	@echo "[info] Waiting for database to be ready..."
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
	  if $(DC_FULL) exec -T $(PG_SERVICE) sh -c 'pg_isready -U "$$POSTGRES_USER" -d "$${POSTGRES_DB:-postgres}" > /dev/null 2>&1'; then \
	    echo "[info] Database is ready"; break; \
	  fi; \
	  echo "[info] Waiting for database... (attempt $$i/10)"; \
	  sleep 2; \
	done
	@MARKER_EXISTS=$$($(DC_FULL) exec -T $(PG_SERVICE) sh -c 'psql -U "$$POSTGRES_USER" -d "$${POSTGRES_DB:-postgres}" -tAc "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema='"'"'public'"'"' AND table_name='"'"'schema_baseline_meta'"'"');"'); \
	if [ "$$MARKER_EXISTS" = "t" ]; then \
	  echo "[info] Baseline already applied (marker table exists)"; \
	else \
	  echo "[info] Baseline not applied, checking for partial state..."; \
	  STG_EXISTS=$$($(DC_FULL) exec -T $(PG_SERVICE) sh -c 'psql -U "$$POSTGRES_USER" -d "$${POSTGRES_DB:-postgres}" -tAc "SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name='"'"'stg'"'"');"'); \
	  if [ "$$STG_EXISTS" = "t" ]; then \
	    echo "[error] stg schema exists but marker table is missing!"; \
	    echo "[error] This indicates a partial/broken state. Please run:"; \
	    echo "        make down ENV=$(ENV)"; \
	    echo "        docker volume rm $(ENV)_db_data"; \
	    echo "        make up ENV=$(ENV)"; \
	    exit 1; \
	  fi; \
	  if [ "$(ENV_CANON)" = "vm_prod" ] && [ "$(FORCE)" != "1" ]; then \
	    echo "[error] vm_prod requires FORCE=1 to apply baseline (prevent accidents)"; exit 1; \
	  fi; \
	  echo "[info] Applying baseline schema..."; \
	  BASELINE_SHA256=$$(sha256sum "$(BASELINE_SQL)" | awk '{print $$1}'); \
	  $(DC_FULL) cp $(BASELINE_SQL) $(PG_SERVICE):/tmp/schema_baseline.sql; \
	  $(DC_FULL) exec -T $(PG_SERVICE) sh -c '\
	    psql -U "$$POSTGRES_USER" -d "$${POSTGRES_DB:-postgres}" \
	         -v ON_ERROR_STOP=1 \
	         -f /tmp/schema_baseline.sql'; \
	  $(DC_FULL) exec -T $(PG_SERVICE) sh -c '\
	    psql -U "$$POSTGRES_USER" -d "$${POSTGRES_DB:-postgres}" -c \
	      "CREATE TABLE IF NOT EXISTS public.schema_baseline_meta( \
	         id bigserial primary key, \
	         applied_at timestamptz not null default now(), \
	         baseline_path text not null, \
	         baseline_sha256 text not null \
	       ); \
	       INSERT INTO public.schema_baseline_meta(baseline_path, baseline_sha256) \
	       VALUES ('"'"'$(BASELINE_SQL)'"'"', '"'"''"$$BASELINE_SHA256"''"'"');"'; \
	  $(DC_FULL) exec -T $(PG_SERVICE) rm -f /tmp/schema_baseline.sql; \
	  echo "[ok] Baseline applied successfully"; \
	fi

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
## ※ migrations_v2 を使用（legacy migrations/ は削除済み）
## 使い方:
##   make al-cur-env ENV=vm_stg
##   make al-up-env  ENV=vm_stg
##   make al-up-env  ENV=vm_prod
## ------------------------------------------------------------
ALEMBIC_INI ?= /backend/migrations_v2/alembic.ini
ALEMBIC_ENV := $(DC_FULL) exec core_api alembic -c $(ALEMBIC_INI)

al-up-env: check
	@echo "[info] Ensuring baseline schema exists..."
	@$(MAKE) db-ensure-baseline-env ENV=$(ENV) FORCE=$(FORCE)
	@echo "[info] Running DB roles bootstrap..."
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
## ※ migrations_v2 を使用（legacy migrations/ は削除済み）
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
## Alembic v2: Advanced DB Management (Baseline-first)
## ============================================================
## ⚠️ 注意:
##   - migrations_v2 が標準になりました（legacy migrations/ は削除済み）
##   - 通常のマイグレーションには al-up-env / al-cur-env などを使用
##   - このセクションは特殊操作（スナップショット適用など）のみ
##
## 新規環境構築（スナップショットから）:
##   1. make db-apply-snapshot-v2-env ENV=vm_stg
##   2. make db-bootstrap-roles-env ENV=vm_stg
##   3. make al-stamp-v2-env ENV=vm_stg REV=0001_baseline
##   4. make al-up-v2-env ENV=vm_stg
##
## 通常のマイグレーション:
##   make al-up-env ENV=local_dev   # migrations_v2 を使用
##   make al-cur-env ENV=vm_stg     # migrations_v2 を使用
##
## 注意:
##   - vm_prod の初期化には FORCE=1 が必須（誤操作防止）
## ============================================================

ALEMBIC_V2_INI ?= /backend/migrations_v2/alembic.ini
ALEMBIC_V2_ENV := $(DC_FULL) exec core_api alembic -c $(ALEMBIC_V2_INI)
BASELINE_SQL   := app/backend/core_api/migrations_v2/sql/schema_baseline.sql

.PHONY: al-up-v2-env al-down-v2-env al-cur-v2-env al-hist-v2-env al-heads-v2-env al-stamp-v2-env \
        db-apply-snapshot-v2-env db-init-from-snapshot-v2-env db-reset-volume-v2-env \
        al-up-env-legacy al-down-env-legacy al-cur-env-legacy

## v2 Alembic コマンド（後方互換性のため残存、標準コマンドへのエイリアス）
al-up-v2-env: al-up-env
	@echo "[非推奨] al-up-v2-env は非推奨です。make al-up-env ENV=$(ENV) を使用してください"

al-down-v2-env: al-down-env
	@echo "[非推奨] al-down-v2-env は非推奨です。make al-down-env ENV=$(ENV) を使用してください"

al-cur-v2-env: al-cur-env
	@echo "[非推奨] al-cur-v2-env は非推奨です。make al-cur-env ENV=$(ENV) を使用してください"

al-hist-v2-env: al-hist-env
	@echo "[非推奨] al-hist-v2-env は非推奨です。make al-hist-env ENV=$(ENV) を使用してください"

al-heads-v2-env: al-heads-env
	@echo "[非推奨] al-heads-v2-env は非推奨です。make al-heads-env ENV=$(ENV) を使用してください"

al-stamp-v2-env: check
	@echo "[非推奨] al-stamp-v2-env は非推奨です。make al-stamp-env ENV=$(ENV) REV=$(REV) を使用してください"
	@if [ -z "$(REV)" ]; then \
	  echo "[error] REV is required. Usage: make al-stamp-env ENV=$(ENV) REV=0001_baseline"; \
	  exit 1; \
	fi
	$(ALEMBIC_ENV) stamp $(REV)
	@echo "[ok] Stamped $(ENV) database with revision $(REV)"

## スナップショット適用（ENV追従、危険操作ガード付き）
db-apply-snapshot-v2-env: check
	@if [ "$(ENV_CANON)" = "vm_prod" ] && [ "$(FORCE)" != "1" ]; then \
	  echo "[error] ❌ vm_prod への snapshot 適用には FORCE=1 が必須です"; \
	  echo "[error]    例: make db-apply-snapshot-v2-env ENV=vm_prod FORCE=1"; \
	  exit 1; \
	fi
	@if [ ! -f "$(BASELINE_SQL)" ]; then \
	  echo "[error] ❌ Baseline SQL not found: $(BASELINE_SQL)"; \
	  echo "[error]    Run: ./scripts/db/export_schema_baseline_local_dev.sh"; \
	  exit 1; \
	fi
	@echo "[info] Applying schema baseline to $(ENV) ($(ENV_CANON))..."
	@echo "[info] Copying SQL to container..."
	$(DC_FULL) cp $(BASELINE_SQL) db:/tmp/schema_baseline.sql
	@echo "[info] Executing baseline SQL..."
	$(DC_FULL) exec -T db sh -c '\
	  psql -U "$$POSTGRES_USER" -d "$${POSTGRES_DB:-postgres}" \
	       -v ON_ERROR_STOP=1 \
	       -f /tmp/schema_baseline.sql'
	@echo "[info] Cleaning up temporary file..."
	$(DC_FULL) exec -T db rm -f /tmp/schema_baseline.sql
	@echo "[ok] Schema baseline applied successfully to $(ENV)"

## まとめターゲット: DB初期化 → snapshot適用 → roles bootstrap → stamp
db-init-from-snapshot-v2-env: check
	@if [ "$(ENV_CANON)" = "vm_prod" ] && [ "$(FORCE)" != "1" ]; then \
	  echo "[error] ❌ vm_prod の初期化には FORCE=1 が必須です"; \
	  echo "[error]    例: make db-init-from-snapshot-v2-env ENV=vm_prod FORCE=1"; \
	  exit 1; \
	fi
	@echo "[info] ========================================"
	@echo "[info] DB初期化フロー開始 (ENV=$(ENV))"
	@echo "[info] ========================================"
	@echo "[info] Step 1/5: 環境停止..."
	@$(MAKE) down ENV=$(ENV)
	@echo "[info] Step 2/5: DBボリューム削除..."
	@$(MAKE) db-reset-volume-v2-env ENV=$(ENV) FORCE=$(FORCE)
	@echo "[info] Step 3/5: 環境起動..."
	@$(MAKE) up ENV=$(ENV)
	@echo "[info] Step 4/5: スナップショット適用..."
	@$(MAKE) db-apply-snapshot-v2-env ENV=$(ENV) FORCE=$(FORCE)
	@echo "[info] Step 5/5: Roles bootstrap..."
	@$(MAKE) db-bootstrap-roles-env ENV=$(ENV)
	@echo "[ok] ========================================"
	@echo "[ok] DB初期化完了。次のコマンドを実行してください:"
	@echo "[ok]   make al-stamp-v2-env ENV=$(ENV) REV=0001_baseline"
	@echo "[ok]   make al-up-v2-env ENV=$(ENV)"
	@echo "[ok] ========================================"

## 危険操作: DBボリューム削除（vm_prodはFORCE必須）
db-reset-volume-v2-env:
	@if [ "$(ENV_CANON)" = "vm_prod" ] && [ "$(FORCE)" != "1" ]; then \
	  echo "[error] ❌ vm_prod のボリューム削除には FORCE=1 が必須です"; \
	  echo "[error]    例: make db-reset-volume-v2-env ENV=vm_prod FORCE=1"; \
	  exit 1; \
	fi
	@echo "[warning] ⚠️  Removing postgres volume for $(ENV)..."
	docker volume rm $(ENV)_postgres_data || true
	@echo "[ok] Volume removed (if it existed)"

## ============================================================
## Legacy Alembic Commands（削除済み migrations/ への参照）
## ============================================================
## 注意:
##   - legacy migrations/ フォルダは完全に削除されました
##   - これらのコマンドはエラーメッセージを表示するのみです
##   - 標準コマンド（al-*-env）が migrations_v2 を使用します
## ============================================================

al-up-env-legacy:
	@echo "❌ [ERROR] legacy migrations/ フォルダは削除されました" && \
	echo "   migrations_v2 を使用してください: make al-up-env ENV=$(ENV)" && \
	exit 1

al-down-env-legacy:
	@echo "❌ [ERROR] legacy migrations/ フォルダは削除されました" && \
	echo "   migrations_v2 を使用してください: make al-down-env ENV=$(ENV)" && \
	exit 1

al-cur-env-legacy:
	@echo "❌ [ERROR] legacy migrations/ フォルダは削除されました" && \
	echo "   migrations_v2 を使用してください: make al-cur-env ENV=$(ENV)" && \
	exit 1

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
	  -t $(STG_IMAGE_REGISTRY)/inbound_forecast_worker:$(STG_IMAGE_TAG) \
	  -f app/backend/inbound_forecast_worker/Dockerfile --target stg app/backend
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
	  -t $(PROD_IMAGE_REGISTRY)/inbound_forecast_worker:$(PROD_IMAGE_TAG) \
	  -f app/backend/inbound_forecast_worker/Dockerfile --target prod app/backend
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
	@for svc in core_api plan_worker inbound_forecast_worker ai_api ledger_api rag_api manual_api nginx; do \
	  echo "  -> push $(PROD_IMAGE_REGISTRY)/$$svc:$(PROD_IMAGE_TAG)"; \
	  docker push $(PROD_IMAGE_REGISTRY)/$$svc:$(PROD_IMAGE_TAG); \
	done

publish-prod-images: build-prod-images push-prod-images
	@echo "[ok] PROD images built & pushed (tag=$(PROD_IMAGE_TAG))"

## ============================================================
## Git ref (tag/commit) から checkout せずに build & push する
##   - git worktree を一時作成して、その中で既存ターゲットを実行
##   - 使い方（例）:
##       NO_CACHE=1 PULL=1 make publish-stg-images-from-ref GIT_REF=v1.2.3
##       NO_CACHE=1 PULL=1 make publish-stg-images-from-ref GIT_REF=3ef33710 STG_IMAGE_TAG=stg-latest
##       NO_CACHE=1 PULL=1 make publish-prod-images-from-ref GIT_REF=v1.2.3
## ============================================================

.PHONY: publish-stg-images-from-ref publish-prod-images-from-ref

# 一時worktreeの親ディレクトリ（必要に応じて変更）
WORKTREE_TMP_BASE ?= /tmp/sanbou_worktree

publish-stg-images-from-ref:
	@if [ -z "$(GIT_REF)" ]; then \
	  echo "[error] GIT_REF is required. e.g. make $@ GIT_REF=v1.2.3"; \
	  exit 1; \
	fi
	@bash -c 'set -euo pipefail; \
	mkdir -p "$(WORKTREE_TMP_BASE)"; \
	WT_DIR="$$(mktemp -d $(WORKTREE_TMP_BASE)/stg_build_XXXXXX)"; \
	cleanup() { \
	  echo "[info] cleanup worktree $$WT_DIR"; \
	  git -C "$(CURDIR)" worktree remove -f "$$WT_DIR" >/dev/null 2>&1 || true; \
	  rm -rf "$$WT_DIR" >/dev/null 2>&1 || true; \
	}; \
	trap cleanup EXIT; \
	echo "[info] fetch tags..."; \
	git -C "$(CURDIR)" fetch --tags --prune; \
	echo "[info] create worktree: ref=$(GIT_REF) dir=$$WT_DIR"; \
	git -C "$(CURDIR)" worktree add --detach "$$WT_DIR" "$(GIT_REF)"; \
	DEFAULT_TAG="stg-$$(echo "$(GIT_REF)" | tr "/:@" "---")"; \
	TAG_TO_USE="$${STG_IMAGE_TAG:-$$DEFAULT_TAG}"; \
	echo "[info] build&push STG from ref=$(GIT_REF) tag=$$TAG_TO_USE"; \
	( cd "$$WT_DIR" && \
	  NO_CACHE="$(NO_CACHE)" PULL="$(PULL)" \
	  $(MAKE) --no-print-directory publish-stg-images STG_IMAGE_TAG="$$TAG_TO_USE" \
	); \
	echo "[ok] publish-stg-images-from-ref done (ref=$(GIT_REF), tag=$$TAG_TO_USE)"'

publish-prod-images-from-ref:
	@if [ -z "$(GIT_REF)" ]; then \
	  echo "[error] GIT_REF is required. e.g. make $@ GIT_REF=v1.2.3"; \
	  exit 1; \
	fi
	@bash -c 'set -euo pipefail; \
	mkdir -p "$(WORKTREE_TMP_BASE)"; \
	WT_DIR="$$(mktemp -d $(WORKTREE_TMP_BASE)/prod_build_XXXXXX)"; \
	cleanup() { \
	  echo "[info] cleanup worktree $$WT_DIR"; \
	  git -C "$(CURDIR)" worktree remove -f "$$WT_DIR" >/dev/null 2>&1 || true; \
	  rm -rf "$$WT_DIR" >/dev/null 2>&1 || true; \
	}; \
	trap cleanup EXIT; \
	echo "[info] fetch tags..."; \
	git -C "$(CURDIR)" fetch --tags --prune; \
	echo "[info] create worktree: ref=$(GIT_REF) dir=$$WT_DIR"; \
	git -C "$(CURDIR)" worktree add --detach "$$WT_DIR" "$(GIT_REF)"; \
	DEFAULT_TAG="prod-$$(echo "$(GIT_REF)" | tr "/:@" "---")"; \
	TAG_TO_USE="$${PROD_IMAGE_TAG:-$$DEFAULT_TAG}"; \
	echo "[info] build&push PROD from ref=$(GIT_REF) tag=$$TAG_TO_USE"; \
	( cd "$$WT_DIR" && \
	  NO_CACHE="$(NO_CACHE)" PULL="$(PULL)" \
	  $(MAKE) --no-print-directory publish-prod-images PROD_IMAGE_TAG="$$TAG_TO_USE" \
	); \
	echo "[ok] publish-prod-images-from-ref done (ref=$(GIT_REF), tag=$$TAG_TO_USE)"'

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
	@for svc in core_api plan_worker inbound_forecast_worker ai_api ledger_api rag_api manual_api nginx; do \
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

## ============================================================
## 日次予測: Lookback期間別精度比較実験
## ============================================================
## 使い方:
##   make forecast-lookback-sweep END=2025-12-17
##   make forecast-lookback-sweep END=2025-12-17 QUICK=1
##   make forecast-lookback-sweep END=2025-12-17 LOOKBACKS=90,180,360
##
## オプション:
##   END       - 評価基準日（必須、YYYY-MM-DD形式）
##   LOOKBACKS - カンマ区切りのlookback日数（デフォルト: 60,90,120,180,270,360）
##   QUICK     - 1を指定すると軽量モード
##   EVAL_DAYS - 評価期間日数（デフォルト: 90）
##
## 出力:
##   tmp/experiments/lookback/results.csv - 結果CSV
##   tmp/experiments/lookback/report.md   - レポート
## ============================================================
END ?=
LOOKBACKS ?= 60,90,120,180,270,360
QUICK ?=
EVAL_DAYS ?= 90

forecast-lookback-sweep:
ifndef END
	@echo "[error] END is required. Usage: make forecast-lookback-sweep END=2025-12-17"
	@exit 1
endif
	@echo "=== Running Lookback Sweep Experiment ==="
	@echo "END_DATE: $(END)"
	@echo "LOOKBACKS: $(LOOKBACKS)"
	@echo "QUICK: $(if $(QUICK),Yes,No)"
	$(DC_FULL) exec inbound_forecast_worker python3 /backend/scripts/experiments/run_lookback_sweep.py \
		--end-date $(END) \
		--lookbacks $(LOOKBACKS) \
		--eval-days $(EVAL_DAYS) \
		$(if $(QUICK),--quick,) \
		--db-connection-string "postgresql+psycopg://sanbou_app_dev:rwT8ovWmhwLctRNuPynH4jOoYSwXvVvc2czeGC0Zos4=@db:5432/sanbou_dev"
	@echo "=== Experiment Completed ==="
	@echo "Results: tmp/experiments/lookback/results.csv"
	@echo "Report: tmp/experiments/lookback/report.md"
