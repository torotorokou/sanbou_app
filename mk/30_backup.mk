## =============================================================
## mk/30_backup.mk - Database backup and restore
## =============================================================
## 注意:
##   - POSTGRES_USER と POSTGRES_DB は各環境の .env ファイルから自動取得
##   - 環境変数から動的に取得されるため、ユーザー名はハードコードされていません
##   - 各環境の .env ファイルで POSTGRES_USER と POSTGRES_DB を設定してください
## =============================================================

##@ Backup

.PHONY: backup restore-from-dump restore-from-sql

DATE        := $(shell date +%F_%H%M%S)
BACKUP_DIR  ?= /mnt/c/Users/synth/Desktop/backups
PG_SERVICE  ?= db

backup: ## Create pg_dump backup (backups/ENV_TIMESTAMP.dump)
	@echo "[info] logical backup (pg_dump) ENV=$(ENV)"
	@mkdir -p "$(BACKUP_DIR)"
	$(DC_FULL) exec -T $(PG_SERVICE) sh -c '\
	  pg_dump -U "$$POSTGRES_USER" -d "$${POSTGRES_DB:-postgres}" \
	    --format=custom --file=/tmp/backup.dump'
	$(DC_FULL) cp $(PG_SERVICE):/tmp/backup.dump \
	  "$(BACKUP_DIR)/$(ENV)_$(DATE).dump"
	@$(DC_FULL) exec -T $(PG_SERVICE) rm -f /tmp/backup.dump || true
	@echo "[ok] backup -> $(BACKUP_DIR)/$(ENV)_$(DATE).dump"

DUMP ?= backups/sanbou_dev_2025-12-03.dump

restore-from-dump: check ## Restore from pg_dump file (DUMP=backups/xxx.dump)
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
SQL ?=

restore-from-sql: check ## Restore from SQL file (SQL=backups/xxx.sql)
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
