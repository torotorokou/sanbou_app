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

SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c

ENV ?= dev
ENV := $(strip $(ENV))
DC := docker compose
OVERRIDE := docker/docker-compose.$(ENV).yml
ENV_FILE_COMMON := env/.env.common
ENV_FILE := env/.env.$(ENV)
COMPOSE_FILES := -f $(OVERRIDE)
# 追加: Secrets 自動注入用ファイル (Git 管理外)
SECRETS_FILE := secrets/.env.$(ENV).secrets
COMPOSE_ENV_ARGS := --env-file $(ENV_FILE_COMMON) --env-file $(ENV_FILE) --env-file $(SECRETS_FILE)

.PHONY: up down logs ps rebuild config ledger_startup secrets gh-secrets

check:
	@if [ ! -f "$(OVERRIDE)" ]; then echo "[error] $(OVERRIDE) not found"; exit 1; fi
	@if [ ! -f "$(ENV_FILE_COMMON)" ]; then echo "[error] $(ENV_FILE_COMMON) not found"; exit 1; fi
	@if [ ! -f "$(ENV_FILE)" ]; then echo "[error] $(ENV_FILE) not found"; exit 1; fi
	# --- Port availability check (dev/stg) ---------------------------------
	@if [ "$(ENV)" = "dev" ]; then
	  # dev は nginx を公開しないため Vite と DB のポートのみチェック
	  PORTS="$${DEV_VITE_PORT:-5173} $${DEV_DB_PORT:-5432}"
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
	$(DC) $(COMPOSE_ENV_ARGS) -p $(ENV) $(COMPOSE_FILES) up -d --build --remove-orphans
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


# -------------------------------------------------------------
# secrets: GCP Secret Manager から OPENAI / GEMINI を取得し secrets/.env.<env>.secrets 生成
# - 再生成条件: ファイル不存在 or 空行含む未設定 / 強制再生成は REGENERATE=1 make ...
# -------------------------------------------------------------
secrets:
	@if [ "$(ENV)" != "dev" ] && [ "$(ENV)" != "stg" ] && [ "$(ENV)" != "prod" ]; then \
	  echo "[error] unsupported ENV '$(ENV)'"; exit 2; fi
	@mkdir -p secrets
	@if [ "$(REGENERATE)" = "1" ] || [ ! -s "$(SECRETS_FILE)" ]; then \
	  ( set +e; \
	    if command -v gcloud >/dev/null 2>&1; then \
	      echo "[info] generating $(SECRETS_FILE) from Secret Manager"; \
	      GEMINI=$$(gcloud secrets versions access latest --secret=gemini-api-key 2>/dev/null | tr -d '\n'); STATUS1=$$?; \
	      OPENAI=$$(gcloud secrets versions access latest --secret=openai-api-key 2>/dev/null | tr -d '\n'); STATUS2=$$?; \
	      if [ $$STATUS1 -ne 0 ] || [ $$STATUS2 -ne 0 ]; then echo "[warn] secret access failed (statuses $$STATUS1 $$STATUS2) -> using empty placeholders"; GEMINI=""; OPENAI=""; fi; \
	    else \
	      echo "[warn] gcloud not found; creating empty $(SECRETS_FILE)"; GEMINI=""; OPENAI=""; \
	    fi; \
	    { echo "# Auto-generated $(SECRETS_FILE)"; echo "# DO NOT COMMIT"; echo "GEMINI_API_KEY=$$GEMINI"; echo "OPENAI_API_KEY=$$OPENAI"; } > $(SECRETS_FILE).tmp; \
	    mv $(SECRETS_FILE).tmp $(SECRETS_FILE); chmod 600 $(SECRETS_FILE); echo "[info] wrote $(SECRETS_FILE)"; \
	  ); \
	else echo "[info] reuse existing $(SECRETS_FILE)"; fi
	@# マスク表示
	@head_gemini=$$(grep '^GEMINI_API_KEY=' $(SECRETS_FILE) | cut -d= -f2 | sed 's/\(......\).*/\1****/'); \
	 head_openai=$$(grep '^OPENAI_API_KEY=' $(SECRETS_FILE) | cut -d= -f2 | sed 's/\(......\).*/\1****/'); \
	 echo "[info] GEMINI_API_KEY=$$head_gemini OPENAI_API_KEY=$$head_openai"

rebuild: check secrets
	@echo "[info] REBUILD (ENV=$(ENV))"
	$(DC) $(COMPOSE_ENV_ARGS) -p $(ENV) $(COMPOSE_FILES) build --no-cache
	$(DC) $(COMPOSE_ENV_ARGS) -p $(ENV) $(COMPOSE_FILES) up -d --force-recreate --remove-orphans
	@echo "[info] done"

config: check secrets
	$(DC) $(COMPOSE_ENV_ARGS) -p $(ENV) $(COMPOSE_FILES) config

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

# -------------------------------------------------------------
# gh-secrets: GitHub Environments へ .env.common をロード
# 例:
#   make gh-secrets ENV=stg REPO=torotorokou/sanbou_app FILE=env/.env.common PREFIX=
#   make gh-secrets JSON=scripts/examples/secrets.json
# -------------------------------------------------------------
gh-secrets:
	@set +u; \
	REPO_VAL=$${REPO:-}; JSON_VAL=$${JSON:-}; CSV_VAL=$${CSV:-}; PREFIX_VAL=$${PREFIX:-}; DRY_VAL=$${DRY:-}; \
	FILE_VAL="$${FILE:-}"; \
	DRY_FLAG=""; if [ "$$DRY_VAL" = "1" ]; then DRY_FLAG="--dry-run"; fi; \
	# --- JSON/CSV モード（複数環境を一括投入） ------------------------------ \
	if [ -n "$$JSON_VAL" ]; then \
	  echo "[info] Apply from JSON ($$JSON_VAL)"; \
	  ./scripts/gh_env_secrets_sync.sh --repo "$$REPO_VAL" --json "$$JSON_VAL" --prefix "$$PREFIX_VAL" $$DRY_FLAG; \
	elif [ -n "$$CSV_VAL" ]; then \
	  echo "[info] Apply from CSV ($$CSV_VAL)"; \
	  ./scripts/gh_env_secrets_sync.sh --repo "$$REPO_VAL" --csv "$$CSV_VAL" --prefix "$$PREFIX_VAL" $$DRY_FLAG; \
	# --- 単一環境モード（.env.common + .env.<env> を順番に適用） ------------ \
	else \
	  COMMON_FILE="env/.env.common"; SPEC_FILE="env/.env.$(ENV)"; \
	  # FILE が指定されていれば単一ファイル適用（上級者向け）。未指定なら 2 ファイル適用。 \
	  if [ -n "$$FILE_VAL" ]; then \
	    echo "[info] Apply single env ($(ENV)) from $$FILE_VAL"; \
	    ./scripts/gh_env_secrets_sync.sh --repo "$$REPO_VAL" --env "$(ENV)" --file "$$FILE_VAL" --prefix "$$PREFIX_VAL" $$DRY_FLAG; \
	  else \
	    # 1) 共通 .env を先に適用（後続で環境別が上書き） \
	    if [ ! -f "$$COMMON_FILE" ]; then echo "[error] $$COMMON_FILE not found"; exit 2; fi; \
	    echo "[info] Apply common: $$COMMON_FILE -> environment '$(ENV)'"; \
	    ./scripts/gh_env_secrets_sync.sh --repo "$$REPO_VAL" --env "$(ENV)" --file "$$COMMON_FILE" --prefix "$$PREFIX_VAL" $$DRY_FLAG; \
	    # 2) 環境別 .env を適用（同一キーがあれば上書き） \
	    if [ ! -f "$$SPEC_FILE" ]; then echo "[error] $$SPEC_FILE not found"; exit 2; fi; \
	    echo "[info] Apply specific: $$SPEC_FILE -> environment '$(ENV)'"; \
	    ./scripts/gh_env_secrets_sync.sh --repo "$$REPO_VAL" --env "$(ENV)" --file "$$SPEC_FILE" --prefix "$$PREFIX_VAL" $$DRY_FLAG; \
	  fi; \
	fi
