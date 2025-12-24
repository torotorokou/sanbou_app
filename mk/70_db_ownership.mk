## ============================================================
## DB 権限管理（ops/db/sql/ 配下の SQL スクリプト実行）
## ============================================================
## 目的: PostgreSQL のロール/所有者/権限設計を整理
##       「権限エラーが頻発する状態」を根絶
##
## 実行順序:
##   make db-fix-ownership ENV=local_dev       # 全スクリプト実行
##   make db-fix-ownership ENV=local_dev STEP=1 # 01_roles.sql のみ実行
##   make db-verify-ownership ENV=local_dev    # 検証
##
## ステップ:
##   STEP=1: 01_roles.sql            - sanbou_owner ロール作成
##   STEP=2: 02_reassign_ownership.sql - owner を sanbou_owner に移管
##   STEP=3: 03_grants.sql           - アプリユーザーへの権限付与
##   STEP=4: 04_default_privileges.sql - 新規オブジェクトへの自動権限付与
##
## ============================================================

##@ DB Ownership

.PHONY: db-fix-ownership db-verify-ownership

DB_OPS_SQL_DIR := ops/db/sql

# アプリユーザー名を ENV から自動決定
ifeq ($(ENV_CANON),local_dev)
	DB_APP_USER := sanbou_app_dev
endif
ifeq ($(ENV_CANON),vm_stg)
	DB_APP_USER := sanbou_app_stg
endif
ifeq ($(ENV_CANON),vm_prod)
	DB_APP_USER := sanbou_app_prod
endif

db-fix-ownership: check ## Fix database ownership and permissions (STEP=N for single step)
	@echo "[info] DB Ownership Refactoring (ENV=$(ENV), app_user=$(DB_APP_USER))"
	@if [ -z "$(DB_APP_USER)" ]; then \
	  echo "[error] ❌ ENV=$(ENV) はサポートされていません"; \
	  exit 1; \
	fi
	@if [ -n "$(STEP)" ]; then \
	  PADDED_STEP=$$(printf "%02d" $(STEP)); \
	  SQL_FILE="$(DB_OPS_SQL_DIR)/$${PADDED_STEP}_*.sql"; \
	  MATCHED_FILE=$$(ls $$SQL_FILE 2>/dev/null | head -n 1); \
	  if [ -z "$$MATCHED_FILE" ]; then \
	    echo "[error] ❌ STEP=$(STEP) に対応する SQL ファイルが見つかりません"; \
	    exit 1; \
	  fi; \
	  echo "[info] Executing: $$MATCHED_FILE"; \
	  $(DC_FULL) cp $$MATCHED_FILE $(PG_SERVICE):/tmp/db_fix.sql; \
	  $(DC_FULL) exec -T $(PG_SERVICE) sh -c '\
	    psql -U myuser -d "$${POSTGRES_DB:-postgres}" \
	         -v ON_ERROR_STOP=0 \
	         -c "SET vars.app_user TO '"'"'$(DB_APP_USER)'"'"'" \
	         -c "SET vars.env TO '"'"'$(ENV_CANON)'"'"'" \
	         -f /tmp/db_fix.sql'; \
	  $(DC_FULL) exec -T $(PG_SERVICE) rm -f /tmp/db_fix.sql; \
	  echo "[ok] STEP=$(STEP) completed"; \
	else \
	  for sql_file in $(DB_OPS_SQL_DIR)/0[1-4]_*.sql; do \
	    if [ ! -f "$$sql_file" ]; then continue; fi; \
	    echo "[info] Executing: $$sql_file"; \
	    $(DC_FULL) cp $$sql_file $(PG_SERVICE):/tmp/db_fix.sql; \
	    $(DC_FULL) exec -T $(PG_SERVICE) sh -c '\
	      psql -U myuser -d "$${POSTGRES_DB:-postgres}" \
	           -v ON_ERROR_STOP=0 \
	           -c "SET vars.app_user TO '"'"'$(DB_APP_USER)'"'"'" \
	           -c "SET vars.env TO '"'"'$(ENV_CANON)'"'"'" \
	           -f /tmp/db_fix.sql'; \
	    $(DC_FULL) exec -T $(PG_SERVICE) rm -f /tmp/db_fix.sql; \
	  done; \
	  echo "[ok] db-fix-ownership completed (all steps)"; \
	fi

db-verify-ownership: check ## Verify database ownership configuration
	@echo "[info] DB Ownership Verification (ENV=$(ENV))"
	$(DC_FULL) cp $(DB_OPS_SQL_DIR)/99_verify.sql $(PG_SERVICE):/tmp/db_verify.sql
	$(DC_FULL) exec -T $(PG_SERVICE) sh -c '\
	  psql -U "$$POSTGRES_USER" -d "$${POSTGRES_DB:-postgres}" \
	       -f /tmp/db_verify.sql'
	$(DC_FULL) exec -T $(PG_SERVICE) rm -f /tmp/db_verify.sql
	@echo "[ok] db-verify-ownership completed"
