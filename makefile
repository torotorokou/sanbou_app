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

.PHONY: up down logs ps rebuild config

check:
	@if [ ! -f "$(OVERRIDE)" ]; then echo "[error] $(OVERRIDE) not found"; exit 1; fi
	@if [ ! -f "$(ENV_FILE)" ]; then echo "[error] $(ENV_FILE) not found"; exit 1; fi

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
