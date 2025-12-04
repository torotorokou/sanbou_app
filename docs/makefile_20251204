## =============================================================
## Makefile: dev / stg / prod 用 docker compose 起動ヘルパ
## -------------------------------------------------------------
## 主なターゲット:
##   make up        ENV=local_dev|local_stg|vm_stg|vm_prod
##   make down      ENV=...
##   make rebuild   ENV=...
##   make backup    ENV=local_dev    # ← 追加：バックアップ
##   make restore-from-dump ENV=local_dev DUMP=backups/sanbou_dev_2025-12-03.dump
## -------------------------------------------------------------

SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c

ENV ?= local_dev
ENV := $(strip $(ENV))
DC := docker compose
BUILDKIT ?= 1
PROGRESS ?= plain
BUILDER_DEFAULT ?=

## =============================================================
## 環境マッピング
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
ENV_FILE := env/.env.$(ENV)

ifeq ($(ENV_CANON),local_dev)
	ENV_FILE := env/.env.local_dev
	COMPOSE_FILES := -f docker/docker-compose.dev.yml
	HEALTH_URL := http://localhost:8001/health
else ifeq ($(ENV_CANON),local_stg)
	ENV_FILE := env/.env.local_stg
	COMPOSE_FILES := -f docker/docker-compose.stg.yml
	HEALTH_PORT := $(if $(STG_NGINX_HTTP_PORT),$(STG_NGINX_HTTP_PORT),8080)
	HEALTH_URL := http://localhost:$(HEALTH_PORT)/health
	STG_ENV_FILE := local_stg
else ifeq ($(ENV_CANON),vm_stg)
	ENV_FILE := env/.env.vm_stg
	COMPOSE_FILES := -f docker/docker-compose.stg.yml
	HEALTH_URL := http://stg.sanbou-app.jp/health
	STG_ENV_FILE := vm_stg
else ifeq ($(ENV_CANON),vm_prod)
	ENV_FILE := env/.env.vm_prod
	COMPOSE_FILES := -f docker/docker-compose.prod.yml
	HEALTH_URL := https://sanbou-app.jp/health
else
	$(error Unsupported ENV: $(ENV))
endif

SECRETS_FILE := secrets/.env.$(ENV).secrets
COMPOSE_ENV_ARGS := --env-file $(ENV_FILE_COMMON) --env-file $(ENV_FILE) --env-file $(SECRETS_FILE)
DC_ENV_PREFIX := $(if $(STG_ENV_FILE),STG_ENV_FILE=$(STG_ENV_FILE) ,)
COMPOSE_FILE_LIST := $(strip $(subst -f ,,$(COMPOSE_FILES)))

.PHONY: up down logs ps rebuild config prune secrets restart backup

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
	$(DC_ENV_PREFIX)$(DC) $(COMPOSE_ENV_ARGS) -p $(ENV) $(COMPOSE_FILES) up -d --build --remove-orphans
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
	$(MAKE) up ENV=$(ENV)

## =============================================================
## secrets / prune / rebuild
## =============================================================
secrets:
	@mkdir -p secrets
	@if [ "$(REGENERATE)" = "1" ] || [ ! -s "$(SECRETS_FILE)" ]; then \
	  echo "[info] generate secrets $(SECRETS_FILE)"; \
	  { echo "# Auto-generated"; echo "GEMINI_API_KEY="; echo "OPENAI_API_KEY="; } > $(SECRETS_FILE); chmod 600 $(SECRETS_FILE); \
	else echo "[info] reuse existing $(SECRETS_FILE)"; fi

prune:
	@echo "[info] prune builder cache + unused images"
	@docker builder prune -af && docker image prune -a -f || true

PULL ?= 0
BUILD_PULL_FLAG := $(if $(filter 1,$(PULL)),--pull,)

rebuild: check
	@echo "[info] rebuild ENV=$(ENV)"
	$(MAKE) down ENV=$(ENV)
	DOCKER_BUILDKIT=$(BUILDKIT) BUILDKIT_PROGRESS=$(PROGRESS) \
	$(DC_ENV_PREFIX)$(DC) $(COMPOSE_ENV_ARGS) -p $(ENV) $(COMPOSE_FILES) build $(BUILD_PULL_FLAG) --no-cache
	DOCKER_BUILDKIT=$(BUILDKIT) BUILDKIT_PROGRESS=$(PROGRESS) \
	$(DC_ENV_PREFIX)$(DC) $(COMPOSE_ENV_ARGS) -p $(ENV) $(COMPOSE_FILES) up -d --remove-orphans
	@echo "[ok] rebuild done"

## =============================================================
## health
## =============================================================
health:
	@echo "[info] health check -> $(HEALTH_URL)"
	@curl -I "$(HEALTH_URL)" || echo "[warn] curl failed"

config: check
	$(DC_ENV_PREFIX)$(DC) $(COMPOSE_ENV_ARGS) -p $(ENV) $(COMPOSE_FILES) config

## =============================================================
## バックアップ関連
## =============================================================
.PHONY: backup backup_pg backup_pg_all backup_pgdata backup_code backup_win_info

DATE := $(shell date +%F)
DESKTOP_WIN := $(shell (powershell.exe -NoProfile -Command "[Environment]::GetFolderPath('Desktop')" || echo) 2>/dev/null | tr -d '\r')
DESKTOP := $(strip $(if $(DESKTOP_WIN),$(shell wslpath -u "$(DESKTOP_WIN)" 2>/dev/null),$(HOME)/Desktop))
BACKUP_DIR := $(DESKTOP)/backup

PG_SERVICE ?= db
PGUSER ?= myuser
PGDB ?= sanbou_dev
PGDATA_HOST ?= data/postgres
DC_FULL := $(DC_ENV_PREFIX)$(DC) $(COMPOSE_ENV_ARGS) -p $(ENV) $(COMPOSE_FILES)
USE_DOCKER_TAR ?= 0

backup: backup_pg backup_pg_all backup_pgdata backup_code
	@echo "[info] backup completed -> $(BACKUP_DIR)"
	@ls -lh "$(BACKUP_DIR)" | head -20 || true

backup_win_info:
	@echo "[info] Windows Desktop detected: $(DESKTOP)"
	@echo "[info] Backup dir: $(BACKUP_DIR)"

backup_pg:
	@echo "[info] logical backup (pg_dump)"
	@mkdir -p "$(BACKUP_DIR)"
	$(DC_FULL) exec -T $(PG_SERVICE) pg_dump -U $(PGUSER) -d $(PGDB) --format=custom --file=/tmp/$(PGDB).dump
	$(DC_FULL) cp $(PG_SERVICE):/tmp/$(PGDB).dump "$(BACKUP_DIR)/$(PGDB)_$(DATE).dump"
	@echo "[ok] $(BACKUP_DIR)/$(PGDB)_$(DATE).dump"

backup_pg_all:
	@echo "[info] full dumpall -> $(BACKUP_DIR)"
	@mkdir -p "$(BACKUP_DIR)"
	$(DC_FULL) exec -T $(PG_SERVICE) pg_dumpall -U $(PGUSER) --globals-only > "$(BACKUP_DIR)/pg_globals_$(DATE).sql"
	$(DC_FULL) exec -T $(PG_SERVICE) pg_dumpall -U $(PGUSER) --clean --if-exists > "$(BACKUP_DIR)/pg_all_$(DATE).sql"
	@echo "[ok] pg_dumpall done"

backup_pgdata:
	@echo "[info] physical backup (PostgreSQL data) -> $(BACKUP_DIR)"
	@mkdir -p "$(BACKUP_DIR)"
	@if [ "$(ENV_CANON)" != "local_dev" ]; then \
	  echo "[warn] 物理バックアップは local_dev 前提のホストバインドのみ対応。"; \
	  exit 0; \
	fi
	@echo "[step] stop db"
	$(DC_FULL) stop $(PG_SERVICE)
	@if [ "$(USE_DOCKER_TAR)" = "1" ]; then \
	  echo "[info] docker-run tar mode"; \
	  docker compose -p $(ENV) $(COMPOSE_FILES) $(COMPOSE_ENV_ARGS) \
	    run --rm -v "$$(pwd)/$(PGDATA_HOST)":/pgdata:ro -v "$(BACKUP_DIR)":/backup $(PG_SERVICE) \
	    sh -lc 'tar czf /backup/pgdata_$$(date +%F).tgz -C /pgdata .'; \
	else \
	  if [ -d "$(PGDATA_HOST)" ]; then \
	    echo "[info] try plain tar"; \
	    tar czf "$(BACKUP_DIR)/pgdata_$(DATE).tgz" -C "$(PGDATA_HOST)" . 2>/tmp/_pg_tar.err || true; \
	    if grep -qi "Permission denied" /tmp/_pg_tar.err 2>/dev/null; then \
	      echo "[warn] permission denied -> retry with sudo"; \
	      if command -v sudo >/dev/null 2>&1; then \
	        sudo tar czf "$(BACKUP_DIR)/pgdata_$(DATE).tgz" -C "$(PGDATA_HOST)" . || { \
	          echo "[warn] sudo tar failed -> fallback docker-run"; \
	          docker compose -p $(ENV) $(COMPOSE_FILES) $(COMPOSE_ENV_ARGS) \
	            run --rm -v "$$(pwd)/$(PGDATA_HOST)":/pgdata:ro -v "$(BACKUP_DIR)":/backup $(PG_SERVICE) \
	            sh -lc 'tar czf /backup/pgdata_$$(date +%F).tgz -C /pgdata .'; }; \
	      else \
	        echo "[info] sudo not found -> use docker-run fallback"; \
	        docker compose -p $(ENV) $(COMPOSE_FILES) $(COMPOSE_ENV_ARGS) \
	          run --rm -v "$$(pwd)/$(PGDATA_HOST)":/pgdata:ro -v "$(BACKUP_DIR)":/backup $(PG_SERVICE) \
	          sh -lc 'tar czf /backup/pgdata_$$(date +%F).tgz -C /pgdata .'; \
	      fi; \
	    else echo "[ok] $(BACKUP_DIR)/pgdata_$(DATE).tgz"; fi; \
	    rm -f /tmp/_pg_tar.err || true; \
	  else echo "[warn] $(PGDATA_HOST) not found."; fi; \
	fi
	@echo "[step] start db"
	$(DC_FULL) start $(PG_SERVICE) >/dev/null 2>&1 || true

backup_code:
	@echo "[info] snapshot code/config -> $(BACKUP_DIR)/code_snapshot_$(DATE)"
	@mkdir -p "$(BACKUP_DIR)/code_snapshot_$(DATE)"
	@if [ -d app/backend ]; then \
	  tar czf "$(BACKUP_DIR)/code_snapshot_$(DATE)/backend_$(DATE).tgz" app/backend docker env secrets config 2>/dev/null || true; \
	  echo "[ok] backend snapshot"; \
	fi
	@if [ -d db ]; then \
	  tar czf "$(BACKUP_DIR)/code_snapshot_$(DATE)/sql_$(DATE).tgz" db 2>/dev/null || true; fi
	@if [ -d sql ]; then \
	  tar czf "$(BACKUP_DIR)/code_snapshot_$(DATE)/sql_extra_$(DATE).tgz" sql 2>/dev/null || true; fi
	@echo "[ok] code snapshot done"

## =============================================================
## Restore from custom dump (.dump)
##   使い方:
##     make restore-from-dump ENV=local_dev DUMP=backups/sanbou_dev_2025-12-03.dump
## =============================================================
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
## =============================================================
## PostgreSQL Safe Upgrade (16 -> 17)
## =============================================================
PG_OLD_VOLUME ?= pgdata
PG_NEW_VOLUME ?= pgdata_v17
PG_HOST ?= localhost
PG_PORT ?= 5432

.PHONY: pg.version pg.archive pg.dumpall pg.compose17 pg.up17 pg.restore pg.extensions pg.verify

pg.version:
	@echo "[info] Checking PostgreSQL version in volume: $(PG_OLD_VOLUME)"
	@bash scripts/pg/print_pg_version_in_volume.sh "$(PG_OLD_VOLUME)"

pg.archive:
	@echo "[info] Archiving volume: $(PG_OLD_VOLUME)"
	@bash scripts/pg/archive_volume_tar.sh "$(PG_OLD_VOLUME)"

pg.dumpall:
	@echo "[info] Running pg_dumpall from volume: $(PG_OLD_VOLUME)"
	@bash scripts/pg/dumpall_from_v16.sh "$(PG_OLD_VOLUME)"

pg.compose17:
	@echo ">>> Creating compose override for Postgres 17"
	@echo "# =============================================================" > docker-compose.pg17.yml
	@echo "# docker-compose.pg17.yml" >> docker-compose.pg17.yml
	@echo "# PostgreSQL 17 Upgrade Override" >> docker-compose.pg17.yml
	@echo "# WARNING: DO NOT RUN 'docker compose down -v'" >> docker-compose.pg17.yml
	@echo "#          This will DELETE your old volume!" >> docker-compose.pg17.yml
	@echo "# =============================================================" >> docker-compose.pg17.yml
	@echo "" >> docker-compose.pg17.yml
	@echo "services:" >> docker-compose.pg17.yml
	@echo "  db:" >> docker-compose.pg17.yml
	@echo "    image: postgres:17-alpine" >> docker-compose.pg17.yml
	@echo "    volumes:" >> docker-compose.pg17.yml
	@echo "      - $(PG_NEW_VOLUME):/var/lib/postgresql/data" >> docker-compose.pg17.yml
	@echo "" >> docker-compose.pg17.yml
	@echo "volumes:" >> docker-compose.pg17.yml
	@echo "  $(PG_NEW_VOLUME):" >> docker-compose.pg17.yml
	@echo "    driver: local" >> docker-compose.pg17.yml
	@echo "" >> docker-compose.pg17.yml
	@echo "[ok] Created docker-compose.pg17.yml"
	@echo "[info] Review the file before running 'make pg.up17'"
	@echo ""
	@echo "# If using PostGIS, change image to:"
	@echo "#   image: postgis/postgis:17-3.5"

pg.up17:
	@echo "[info] Starting PostgreSQL 17 with new volume"
	@echo "[warn] Make sure you have reviewed docker-compose.pg17.yml"
	@sleep 2
	DOCKER_BUILDKIT=$(BUILDKIT) $(DC_ENV_PREFIX)$(DC) $(COMPOSE_ENV_ARGS) -p $(ENV) $(COMPOSE_FILES) -f docker-compose.pg17.yml up -d db

pg.restore:
	@if [ -z "$(SQL)" ]; then \
	  echo "[error] SQL parameter is required. Usage: make pg.restore SQL=backups/pg/pg_dumpall_YYYYMMDD_HHMMSS.sql"; \
	  exit 1; \
	fi
	@echo "[info] Restoring SQL: $(SQL)"
	@bash scripts/pg/restore_to_v17.sh "$(SQL)"

pg.extensions:
	@echo "[info] Re-enabling extensions"
	@if [ -z "$(PGPASSWORD)" ]; then \
	  echo "[warn] PGPASSWORD not set. You may be prompted for password."; \
	fi
	@PGHOST=$(PG_HOST) PGPORT=$(PG_PORT) psql -U $${PGUSER:-postgres} -d $${PGDATABASE:-postgres} -f sql/extensions_after_restore.sql

pg.verify:
	@echo "========================================="
	@echo "PostgreSQL Version:"
	@echo "========================================="
	@PGHOST=$(PG_HOST) PGPORT=$(PG_PORT) psql -U $${PGUSER:-postgres} -c "SELECT version();" || true
	@echo ""
	@echo "========================================="
	@echo "Databases:"
	@echo "========================================="
	@PGHOST=$(PG_HOST) PGPORT=$(PG_PORT) psql -U $${PGUSER:-postgres} -c "\l" || true
	@echo ""
	@echo "========================================="
	@echo "Extensions:"
	@echo "========================================="
	@PGHOST=$(PG_HOST) PGPORT=$(PG_PORT) psql -U $${PGUSER:-postgres} -d $${PGDATABASE:-postgres} -c "\dx" || true

.PHONY: al-rev al-rev-auto al-up al-down al-cur al-hist al-heads al-stamp

DC = docker compose -f docker/docker-compose.dev.yml -p local_dev
ALEMBIC = $(DC) exec core_api alembic -c /backend/migrations/alembic.ini

# 使い方:
#   make al-rev MSG="manage view: mart.v_xxx"           # REV_IDは自動生成
#   make al-rev MSG="..." REV_ID=20251104_153045123     # 固定REV_IDを明示
MSG ?= update schema
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

# 既存DBに「適用済み印」を付ける
# 使い方: make al-stamp REV=20251104_153045123
al-stamp:
	$(ALEMBIC) stamp $(REV)

## =============================================================
## Local Demo Environment (完全独立環境)
## =============================================================
.PHONY: demo-up demo-down demo-logs demo-ps demo-restart demo-db-shell demo-db-clone-from-dev

DC_DEMO = docker compose -f docker/docker-compose.local_demo.yml -p local_demo
COMPOSE_ENV_ARGS_DEMO = --env-file env/.env.common --env-file env/.env.local_demo --env-file secrets/.env.local_demo.secrets

demo-up:
	@echo "[info] Starting local_demo environment"
	DOCKER_BUILDKIT=$(BUILDKIT) BUILDKIT_PROGRESS=$(PROGRESS) \
	$(DC_DEMO) $(COMPOSE_ENV_ARGS_DEMO) up -d --build --remove-orphans
	@echo "[ok] demo-up done. Access: http://localhost:5174 (frontend), http://localhost:8013/docs (core_api)"

demo-down:
	@echo "[info] Stopping local_demo environment"
	$(DC_DEMO) down --remove-orphans
	@echo "[ok] demo-down done"

demo-logs:
	@echo "[info] Showing logs for local_demo (use Ctrl+C to exit)"
	$(DC_DEMO) logs -f $(S)

demo-ps:
	@echo "[info] Container status for local_demo"
	$(DC_DEMO) ps

demo-restart:
	@echo "[info] Restarting local_demo environment"
	$(MAKE) demo-down
	$(MAKE) demo-up

demo-db-shell:
	@echo "[info] Connecting to local_demo PostgreSQL"
	$(DC_DEMO) exec db psql -U myuser -d sanbou_demo

# local_dev → local_demo への DB クローン
demo-db-clone-from-dev:
	@echo "[info] Cloning DB from local_dev to local_demo"
	@echo "[step 1/5] Dumping local_dev DB..."
	@mkdir -p backup
	docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
	  pg_dump -U myuser -d sanbou_dev --format=custom --file=/tmp/dev_to_demo.dump
	docker compose -f docker/docker-compose.dev.yml -p local_dev cp \
	  db:/tmp/dev_to_demo.dump ./backup/dev_to_demo.dump
	@echo "[step 2/5] Copying dump to local_demo container..."
	$(DC_DEMO) cp ./backup/dev_to_demo.dump db:/tmp/dev_to_demo.dump
	@echo "[step 3/5] Dropping existing sanbou_demo DB (if exists)..."
	-$(DC_DEMO) exec -T db dropdb -U myuser --if-exists sanbou_demo
	@echo "[step 4/5] Creating fresh sanbou_demo DB..."
	$(DC_DEMO) exec -T db createdb -U myuser sanbou_demo
	@echo "[step 5/5] Restoring dump to sanbou_demo..."
	$(DC_DEMO) exec -T db pg_restore -U myuser -d sanbou_demo /tmp/dev_to_demo.dump
	@echo "[ok] DB clone completed. local_dev → local_demo"
	@echo "[info] Cleaning up temporary files..."
	-$(DC_DEMO) exec -T db rm /tmp/dev_to_demo.dump
	@echo "[ok] Done!"

# =============================================================
# Materialized View Refresh (daily ETL batch)
# =============================================================
.PHONY: refresh-mv refresh-mv-target-card

# 全てのマテリアライズドビューをリフレッシュ（ETL完了後に実行）
refresh-mv:
	@echo "[refresh-mv] Refreshing all materialized views..."
	$(DC) exec -T db psql -U myuser -d sanbou_dev -c "REFRESH MATERIALIZED VIEW CONCURRENTLY mart.mv_target_card_per_day;"
	$(DC) exec -T db psql -U myuser -d sanbou_dev -c "REFRESH MATERIALIZED VIEW CONCURRENTLY mart.mv_inb5y_week_profile_min;"
	$(DC) exec -T db psql -U myuser -d sanbou_dev -c "REFRESH MATERIALIZED VIEW CONCURRENTLY mart.mv_inb_avg5y_day_biz;"
	$(DC) exec -T db psql -U myuser -d sanbou_dev -c "REFRESH MATERIALIZED VIEW CONCURRENTLY mart.mv_inb_avg5y_weeksum_biz;"
	$(DC) exec -T db psql -U myuser -d sanbou_dev -c "REFRESH MATERIALIZED VIEW CONCURRENTLY mart.mv_inb_avg5y_day_scope;"
	@echo "[ok] All materialized views refreshed"

# 目標カードMVのみリフレッシュ（個別実行用）
refresh-mv-target-card:
	@echo "[refresh-mv-target-card] Refreshing mart.mv_target_card_per_day..."
	$(DC) exec -T db psql -U myuser -d sanbou_dev -c "REFRESH MATERIALIZED VIEW CONCURRENTLY mart.mv_target_card_per_day;"
	@echo "[ok] mv_target_card_per_day refreshed"

# =============================================================
# Alembic: Schema Dump & Management
# =============================================================
.PHONY: al-dump-schema-current al-init-from-schema

# 最新スキーマをsql_current/schema_head.sqlにダンプ
al-dump-schema-current:
	@echo "[info] Dumping current schema to sql_current/schema_head.sql"
	@bash scripts/db/dump_schema_current.sh

# 新規環境をschema_head.sqlから初期化（データなし・スキーマのみ）
al-init-from-schema:
	@echo "[info] Initializing database from schema_head.sql"
	@if [ ! -f app/backend/core_api/migrations/alembic/sql_current/schema_head.sql ]; then \
	  echo "[error] schema_head.sql not found. Run 'make al-dump-schema-current' first."; \
	  exit 1; \
	fi
	$(DC) exec -T db psql -U myuser -d sanbou_dev < app/backend/core_api/migrations/alembic/sql_current/schema_head.sql
	@echo "[ok] Schema initialized. Now run: make al-stamp REV=<HEAD_REVISION>"
	@echo "[refresh-mv-target-card] Refreshing mart.mv_target_card_per_day..."
	$(DC) exec -T db psql -U myuser -d sanbou_dev -c "REFRESH MATERIALIZED VIEW CONCURRENTLY mart.mv_target_card_per_day;"
	@echo "[ok] mv_target_card_per_day refreshed"
