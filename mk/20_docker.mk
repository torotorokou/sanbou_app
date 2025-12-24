## =============================================================
## mk/20_docker.mk - Docker Compose operations
## =============================================================

##@ Docker

.PHONY: check up down logs ps restart rebuild pull health config dev-with-nginx

check: ## Check if required files exist
	@for f in $(COMPOSE_FILE_LIST); do \
	  if [ ! -f "$$f" ]; then echo "[error] compose file $$f not found"; exit 1; fi; \
	done
	@if [ ! -f "$(ENV_FILE_COMMON)" ]; then echo "[error] $(ENV_FILE_COMMON) not found"; exit 1; fi
	@if [ ! -f "$(ENV_FILE)" ]; then echo "[error] $(ENV_FILE) not found"; exit 1; fi

up: check ## Start environment (ENV=local_dev/vm_stg/vm_prod/local_demo)
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

down: ## Stop environment
	@echo "[info] DOWN (ENV=$(ENV))"
	@CIDS="$$( $(DC) -p $(ENV) ps -q | wc -l )"; \
	if [ "$$CIDS" -gt 0 ]; then \
	  $(DC) -p $(ENV) down --remove-orphans; \
	else echo "[info] no running containers"; fi

logs: ## Show logs (S=service_name for specific service)
	$(DC) -p $(ENV) logs -f $(S)

ps: ## List containers
	$(DC) -p $(ENV) ps

restart: ## Restart environment (down + up)
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

rebuild: check ## Rebuild and restart (down + build --no-cache + up)
	@echo "[info] rebuild ENV=$(ENV)"
	$(MAKE) down ENV=$(ENV)
	DOCKER_BUILDKIT=$(BUILDKIT) BUILDKIT_PROGRESS=$(PROGRESS) \
	$(DC_FULL) build $(BUILD_PULL_FLAG) --no-cache
	DOCKER_BUILDKIT=$(BUILDKIT) BUILDKIT_PROGRESS=$(PROGRESS) \
	$(DC_FULL) up -d --remove-orphans
	@echo "[ok] rebuild done"

pull: check ## Pull images (for vm_stg/vm_prod)
	@echo "[info] Pulling images (ENV=$(ENV))"
	$(DC_FULL) pull

health: ## Health check
	@echo "[info] health check -> $(HEALTH_URL)"
	@curl -I "$(HEALTH_URL)" || echo "[warn] curl failed"

config: check ## Show resolved docker-compose config
	$(DC_FULL) config

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
dev-with-nginx: ## Start local_dev with nginx (http://localhost:8080)
	@echo "[info] Starting local_dev with nginx (profile: with-nginx)"
	@echo "[info] Access via: http://localhost:8080 (nginx)"
	DOCKER_BUILDKIT=$(BUILDKIT) BUILDKIT_PROGRESS=$(PROGRESS) \
	docker compose -f docker/docker-compose.dev.yml -p local_dev \
	  --env-file env/.env.common --env-file env/.env.local_dev \
	  $(if $(wildcard secrets/.env.local_dev.secrets),--env-file secrets/.env.local_dev.secrets,) \
	  --profile with-nginx up -d --build --remove-orphans
	@echo "[ok] Dev environment with nginx started"
	@echo "[info] Check health: curl http://localhost:8080/health"
