## =============================================================
## mk/50_db_roles.mk - DB Bootstrap: Roles & Permissions
## =============================================================
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
## =============================================================

.PHONY: db-bootstrap-roles-env

BOOTSTRAP_ROLES_SQL ?= scripts/db/bootstrap_roles.sql

db-bootstrap-roles-env: check ## Bootstrap DB roles and permissions (idempotent)
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
