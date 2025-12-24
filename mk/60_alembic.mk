## ============================================================
## Alembic: Database Migrations
## ============================================================

##@ Alembic

.PHONY: al-rev al-rev-auto al-up al-down al-cur al-hist al-heads al-stamp \
        al-up-env al-down-env al-cur-env al-hist-env al-heads-env al-stamp-env \
        al-dump-schema-current al-init-from-schema \
        al-up-v2-env al-down-v2-env al-cur-v2-env al-hist-v2-env al-heads-v2-env al-stamp-v2-env \
        db-apply-snapshot-v2-env db-init-from-snapshot-v2-env db-reset-volume-v2-env \
        al-up-env-legacy al-down-env-legacy al-cur-env-legacy

## ============================================================
## Local Dev Alembic Commands (local_dev 前提)
## ============================================================
ALEMBIC_DC  := docker compose -f docker/docker-compose.dev.yml -p local_dev
ALEMBIC     := $(ALEMBIC_DC) exec core_api alembic -c /backend/migrations/alembic.ini
MSG         ?=
REV_ID      ?=

al-rev: ## Create new migration (manual)
	$(ALEMBIC) revision -m "$(MSG)"

al-rev-auto: ## Create new migration (auto-detect)
	$(ALEMBIC) revision --autogenerate -m "$(MSG)"

al-up: ## Apply migrations (local_dev)
	$(ALEMBIC) upgrade head

al-down: ## Downgrade 1 migration (local_dev)
	$(ALEMBIC) downgrade -1

al-cur: ## Show current migration (local_dev)
	$(ALEMBIC) current

al-hist: ## Show migration history (local_dev)
	$(ALEMBIC) history

al-heads: ## Show migration heads (local_dev)
	$(ALEMBIC) heads

al-stamp: ## Stamp database with revision (local_dev)
	$(ALEMBIC) stamp $(REV_ID)

## ============================================================
## ENV-aware Alembic Commands
## ※ migrations_v2 を使用（legacy migrations/ は削除済み）
## ============================================================
ALEMBIC_INI ?= /backend/migrations/alembic.ini
ALEMBIC_ENV := $(DC_FULL) exec core_api alembic -c $(ALEMBIC_INI)

al-up-env: check ## Apply migrations to ENV (baseline + roles + alembic upgrade)
	@echo "[info] Ensuring baseline schema exists..."
	@$(MAKE) db-ensure-baseline-env ENV=$(ENV) FORCE=$(FORCE)
	@echo "[info] Running DB roles bootstrap..."
	@$(MAKE) db-bootstrap-roles-env ENV=$(ENV)
	@echo "[info] Starting Alembic migration..."
	$(ALEMBIC_ENV) upgrade head

al-down-env: check ## Downgrade 1 migration in ENV
	$(ALEMBIC_ENV) downgrade -1

al-cur-env: check ## Show current migration in ENV
	$(ALEMBIC_ENV) current

al-hist-env: check ## Show migration history in ENV
	$(ALEMBIC_ENV) history

al-heads-env: check ## Show migration heads in ENV
	$(ALEMBIC_ENV) heads

# 既存 DB に「適用済み印」を付ける（ENV追従）
# 使い方: make al-stamp-env ENV=vm_prod REV=<HEAD_REVISION>
al-stamp-env: check ## Stamp database with revision in ENV (REV=xxx)
	$(ALEMBIC_ENV) stamp $(REV)

## ============================================================
## Alembic: Schema Dump & Init (local_dev 前提)
## ※ migrations_v2 を使用（legacy migrations/ は削除済み）
## ============================================================
al-dump-schema-current: ## Dump current schema to sql_current/schema_head.sql
	@echo "[info] Dumping current schema to sql_current/schema_head.sql"
	@bash scripts/db/dump_schema_current.sh

al-init-from-schema: ## Initialize database from schema_head.sql (local_dev)
	@echo "[info] Initializing database from schema_head.sql (local_dev)"
	@if [ ! -f app/backend/core_api/migrations/alembic/sql_current/schema_head.sql ]; then \
	  echo "[error] schema_head.sql not found. Run 'make al-dump-schema-current' first."; \
	  exit 1; \
	fi
	@echo "[info] Using container's POSTGRES_USER environment variable"
	docker compose -f docker/docker-compose.dev.yml -p local_dev \
	  exec -T db sh -c 'psql -U "$$POSTGRES_USER" -d "$${POSTGRES_DB:-sanbou_dev}"' \
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

## v2 Alembic コマンド（後方互換性のため残存、標準コマンドへのエイリアス）
al-up-v2-env: al-up-env ## [Deprecated] Use al-up-env instead
	@echo "[非推奨] al-up-v2-env は非推奨です。make al-up-env ENV=$(ENV) を使用してください"

al-down-v2-env: al-down-env ## [Deprecated] Use al-down-env instead
	@echo "[非推奨] al-down-v2-env は非推奨です。make al-down-env ENV=$(ENV) を使用してください"

al-cur-v2-env: al-cur-env ## [Deprecated] Use al-cur-env instead
	@echo "[非推奨] al-cur-v2-env は非推奨です。make al-cur-env ENV=$(ENV) を使用してください"

al-hist-v2-env: al-hist-env ## [Deprecated] Use al-hist-env instead
	@echo "[非推奨] al-hist-v2-env は非推奨です。make al-hist-env ENV=$(ENV) を使用してください"

al-heads-v2-env: al-heads-env ## [Deprecated] Use al-heads-env instead
	@echo "[非推奨] al-heads-v2-env は非推奨です。make al-heads-env ENV=$(ENV) を使用してください"

al-stamp-v2-env: check ## [Deprecated] Stamp database in ENV (use al-stamp-env instead)
	@echo "[非推奨] al-stamp-v2-env は非推奨です。make al-stamp-env ENV=$(ENV) REV=$(REV) を使用してください"
	@if [ -z "$(REV)" ]; then \
	  echo "[error] REV is required. Usage: make al-stamp-env ENV=$(ENV) REV=0001_baseline"; \
	  exit 1; \
	fi
	$(ALEMBIC_ENV) stamp $(REV)
	@echo "[ok] Stamped $(ENV) database with revision $(REV)"

## スナップショット適用（ENV追従、危険操作ガード付き）
db-apply-snapshot-v2-env: check ## Apply schema baseline to ENV (FORCE=1 for vm_prod)
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
db-init-from-snapshot-v2-env: check ## Initialize DB from snapshot (ENV-aware, FORCE=1 for vm_prod)
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
db-reset-volume-v2-env: ## Remove postgres volume for ENV (FORCE=1 for vm_prod)
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

al-up-env-legacy: ## [ERROR] Legacy migrations/ deleted, use al-up-env
	@echo "❌ [ERROR] legacy migrations/ フォルダは削除されました" && \
	echo "   migrations_v2 を使用してください: make al-up-env ENV=$(ENV)" && \
	exit 1

al-down-env-legacy: ## [ERROR] Legacy migrations/ deleted, use al-down-env
	@echo "❌ [ERROR] legacy migrations/ フォルダは削除されました" && \
	echo "   migrations_v2 を使用してください: make al-down-env ENV=$(ENV)" && \
	exit 1

al-cur-env-legacy: ## [ERROR] Legacy migrations/ deleted, use al-cur-env
	@echo "❌ [ERROR] legacy migrations/ フォルダは削除されました" && \
	echo "   migrations_v2 を使用してください: make al-cur-env ENV=$(ENV)" && \
	exit 1
