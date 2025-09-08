## =============================================================
## Makefile: dev / stg / prod 用 docker compose 起動ヘルパ
## -------------------------------------------------------------
## 主なターゲット:
##   make up        ENV=dev|stg|prod  # コンテナ起動 (デフォルト dev)
##   make down      ENV=...           # 停止
##   make rebuild   ENV=...           # 再ビルド (--no-cache)
##   make logs      ENV=... S=svc     # ログ (S 未指定=全体)
##   make ps        ENV=...           # 稼働中サービス一覧
##   make config    ENV=...           # 最終マージ後 compose 設定表示
## -------------------------------------------------------------
## 変数:
##   ENV (dev/stg/prod) 既定: dev
##   S   logs 対象サービス名 (frontend / ai_api / ledger_api / sql_api / rag_api / nginx)
##   DEV_NGINX_PORT (デフォルト 8080), STG_NGINX_HTTP_PORT (8080), STG_NGINX_HTTPS_PORT (8443)
## -------------------------------------------------------------
## 仕組み:
##   共通: docker-compose.yml
##   環境別 override: docker-compose.<env>.yml
##   dev  : ホットリロード (frontend dev target / backend --reload)
##   stg  : prod 同等構成 (ポートだけ 8080/8443)
##   prod : nginx 80/443 のみ公開
## -------------------------------------------------------------
## 例:
##   make up
##   make up ENV=stg
##   make rebuild ENV=prod
##   make logs ENV=dev S=backend
## =============================================================

SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c

ENV ?= dev
ENV := $(strip $(ENV))
DC := docker compose
BASE := docker/docker-compose.yml
OVERRIDE := docker/docker-compose.$(ENV).yml
ENV_FILE := env/.env.$(ENV)
COMPOSE_FILES := -f $(BASE) -f $(OVERRIDE)

.PHONY: up down logs ps rebuild config ledger_startup

check:
	@if [ ! -f "$(OVERRIDE)" ]; then echo "[error] $(OVERRIDE) not found"; exit 1; fi
	@if [ ! -f "$(ENV_FILE)" ]; then echo "[error] $(ENV_FILE) not found"; exit 1; fi
	# --- Port availability check (dev/stg) ---------------------------------
	@if [ "$(ENV)" = "dev" ]; then
	  PORTS="$${DEV_NGINX_PORT:-8080}"
	elif [ "$(ENV)" = "stg" ]; then
	  # 明示未設定でもデフォルトで 8080/8443 をチェック
	  PORTS="$${STG_NGINX_HTTP_PORT:-8080} $${STG_NGINX_HTTPS_PORT:-8443}"
	else
	  PORTS=""
	fi
	PORTS="`echo $$PORTS | xargs`"
	if [ -n "$$PORTS" ]; then
	  # lsof が無ければ ss で代替
	  if ! command -v lsof >/dev/null 2>&1 && ! command -v ss >/dev/null 2>&1; then
	    echo "[warn] neither lsof nor ss command found; skipping port pre-check" >&2
	  else
	    for P in $$PORTS; do
	      IN_USE=0
	      if command -v lsof >/dev/null 2>&1; then
	        lsof -iTCP:$$P -sTCP:LISTEN >/dev/null 2>&1 && IN_USE=1
	      elif command -v ss >/dev/null 2>&1; then
	        ss -ltn 2>/dev/null | awk '{print $4}' | grep -E ':(|'"$$P"')$$' >/dev/null 2>&1 && IN_USE=1
	      fi
	      if [ $$IN_USE -eq 1 ]; then
	        echo "[error] port $$P already in use by host process."; \
	        echo "        対処例: STG 環境なら 'STG_NGINX_HTTP_PORT=18080 make up ENV=stg' のように空きポートへ変更"; \
	        echo "        使用中プロセス確認: (lsof -iTCP:$$P -sTCP:LISTEN) or (ss -ltn | grep :$$P)"; \
	        exit 2; \
	      fi
	    done
	  fi
	fi

up: check
	@echo "[info] UP (ENV=$(ENV))"
	$(DC) --env-file $(ENV_FILE) -p $(ENV) $(COMPOSE_FILES) up -d --build --remove-orphans
	@echo "[info] done"

down:
	@echo "[info] DOWN (ENV=$(ENV))"
	$(DC) -p $(ENV) down --remove-orphans
	@echo "[info] done"

logs:
	@echo "[info] LOGS (ENV=$(ENV) S=$(S))"
	$(DC) -p $(ENV) logs -f $(S)

ps:
	$(DC) -p $(ENV) ps

rebuild: check
	@echo "[info] REBUILD (ENV=$(ENV))"
	$(DC) --env-file $(ENV_FILE) -p $(ENV) $(COMPOSE_FILES) build --no-cache
	$(DC) --env-file $(ENV_FILE) -p $(ENV) $(COMPOSE_FILES) up -d --force-recreate --remove-orphans
	@echo "[info] done"

config: check
	$(DC) --env-file $(ENV_FILE) -p $(ENV) $(COMPOSE_FILES) config

# -------------------------------------------------------------
# ledger_startup: ledger_api コンテナ内で startup.py (再)実行
# 例: make ledger_startup ENV=stg
# -------------------------------------------------------------
ledger_startup:
	@echo "[info] RUN startup (ENV=$(ENV))"
	# コンテナ名は compose project 名(=ENV) + '_' + service + '_1' 想定
	CID=$$($(DC) -p $(ENV) ps -q ledger_api); \
	if [ -z "$$CID" ]; then echo "[error] ledger_api container not running"; exit 2; fi; \
	$(DC) -p $(ENV) exec -e STAGE=$(ENV) ledger_api python -m app.startup
	@echo "[info] done"
