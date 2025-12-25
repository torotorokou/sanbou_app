## =============================================================
## mk/40_db_baseline.mk - DB Baseline schema setup
## =============================================================
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
## =============================================================

##@ DB

.PHONY: db-ensure-baseline-env

BASELINE_SQL := app/backend/core_api/migrations_v2/sql/schema_baseline.sql

db-ensure-baseline-env: check ## Apply baseline schema if not already applied
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
