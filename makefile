## =============================================================
## Makefile: dev / stg / prod 用 docker compose 起動ヘルパ
## -------------------------------------------------------------
## 主なターゲット:
##   make up        ENV=local_dev|local_stg|vm_stg|vm_prod  # コンテナ起動 (デフォルト local_dev)
##   make down      ENV=...           # 停止
##   make rebuild   ENV=...           # 再ビルド (--no-cache)
##   make logs      ENV=... S=svc     # ログ (S 未指定=全体)
##   make ps        ENV=...           # 稼働中サービス一覧
##   make config    ENV=...           # 最終マージ後 compose 設定表示
## -------------------------------------------------------------

SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c

ENV ?= local_dev
ENV := $(strip $(ENV))
DC := docker compose

# ------------------------------------------------------------------
# Environment mapping (4-tier unified names)
# local_dev  -> 開発 (Vite+reload)
# local_stg  -> ローカル STG パリティ (nginx HTTP)
# vm_stg     -> VM STG (8080/8443 / 未来 TLS)
# vm_prod    -> 本番 (80/443)
# Backward compatibility: 旧 ENV=dev|stg|prod を警告付きで新名称へマップ
# ------------------------------------------------------------------
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

# Compose file set & env file mapping
ifeq ($(ENV_CANON),local_dev)
ENV_FILE := env/.env.local_dev
COMPOSE_FILES := -f docker/docker-compose.dev.yml
HEALTH_URL := http://localhost:8001/health
else ifeq ($(ENV_CANON),local_stg)
ENV_FILE := env/.env.local_stg
COMPOSE_FILES := -f docker/docker-compose.stg.yml
# local_stg では host 側任意ポートへバインドできるため health check を localhost:PORT に動的対応
# ユーザが `STG_NGINX_HTTP_PORT=18080 make rebuild ENV=local_stg` のように指定すると 18080 を使用
HEALTH_PORT := $(if $(STG_NGINX_HTTP_PORT),$(STG_NGINX_HTTP_PORT),8080)
HEALTH_URL := http://localhost:$(HEALTH_PORT)/health
# NOTE: 左詰め必須: タブやスペースでインデントすると GNU make が recipe と誤認し
# "recipe commences before first target" エラーになる可能性があるため列頭に置く
STG_ENV_FILE := local_stg
else ifeq ($(ENV_CANON),vm_stg)
ENV_FILE := env/.env.vm_stg
COMPOSE_FILES := -f docker/docker-compose.stg.yml
HEALTH_URL := http://stg.sanbou-app.jp/health
# NOTE: 上記と同様に左詰めを保持
STG_ENV_FILE := vm_stg
else ifeq ($(ENV_CANON),vm_prod)
ENV_FILE := env/.env.vm_prod
COMPOSE_FILES := -f docker/docker-compose.prod.yml
HEALTH_URL := https://sanbou-app.jp/health
else
$(error Unsupported ENV: $(ENV))
endif

# Secrets file per original ENV name (not canonical) to keep them separate
SECRETS_FILE := secrets/.env.$(ENV).secrets
COMPOSE_ENV_ARGS := --env-file $(ENV_FILE_COMMON) --env-file $(ENV_FILE) --env-file $(SECRETS_FILE)

# docker compose コマンドに渡す追加環境変数 (stg 系で env_file 動的切り替え)
DC_ENV_PREFIX := $(if $(STG_ENV_FILE),STG_ENV_FILE=$(STG_ENV_FILE) ,)

# 展開した compose ファイルリスト (存在チェック用)
COMPOSE_FILE_LIST := $(strip $(subst -f ,,$(COMPOSE_FILES)))

.PHONY: up down logs ps rebuild config ledger_startup secrets gh-secrets prune

check:
	@for f in $(COMPOSE_FILE_LIST); do \
	  if [ ! -f "$$f" ]; then echo "[error] compose file $$f not found"; exit 1; fi; \
	done
	@if [ ! -f "$(ENV_FILE_COMMON)" ]; then echo "[error] $(ENV_FILE_COMMON) not found"; exit 1; fi
	@if [ ! -f "$(ENV_FILE)" ]; then echo "[error] $(ENV_FILE) not found"; exit 1; fi
	# --- Port availability check (dev/stg) ---------------------------------
	@if [ "$(ENV_CANON)" = "local_dev" ]; then
	  # dev は nginx を公開しないため Vite と DB のポートのみチェック
	  PORTS="$${DEV_VITE_PORT:-5173} $${DEV_DB_PORT:-5432}"
	elif [ "$(ENV_CANON)" = "local_stg" ] || [ "$(ENV_CANON)" = "vm_stg" ]; then
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
	        echo "        対処例: STG 環境なら 'STG_NGINX_HTTP_PORT=18080 make up ENV=local_stg' のように空きポートへ変更"; \
	        echo "        使用中プロセス確認: (lsof -iTCP:$$P -sTCP:LISTEN) or (ss -ltn | grep :$$P)"; \
	        exit 2; \
	      fi
	    done
	  fi
	fi

up: check
	@echo "[info] UP (ENV=$(ENV))"
	$(DC_ENV_PREFIX)$(DC) $(COMPOSE_ENV_ARGS) -p $(ENV) $(COMPOSE_FILES) up -d --build --remove-orphans
	@echo "[info] done"

down:
	@echo "[info] DOWN (ENV=$(ENV))"
	@CIDS="$$( $(DC) -p $(ENV) ps -q | wc -l )"; \
	if [ "$$CIDS" -gt 0 ]; then \
	  $(DC) -p $(ENV) down --remove-orphans; \
	  echo "[info] stopped project $(ENV)"; \
	else \
	  echo "[info] no resources for project '$(ENV)'; skipping down"; \
	fi
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
	@if [ "$(ENV_CANON)" != "local_dev" ] && [ "$(ENV_CANON)" != "local_stg" ] && [ "$(ENV_CANON)" != "vm_stg" ] && [ "$(ENV_CANON)" != "vm_prod" ]; then \
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


# -------------------------------------------------------------
# prune: 未使用のビルドキャッシュ/イメージを削除する（安全確認あり）
# 環境変数 PRUNE_CONFIRM=YES を与えると非対話モードで実行できます。
# -------------------------------------------------------------
prune:
	@echo "[info] Docker prune: builder cache + unused images"
	@if [ -t 0 ]; then \
	  read -p "Proceed to delete unused builder cache and images? [y/N]: " yn; \
	else \
	  yn="$${PRUNE_CONFIRM:-n}"; \
	fi; \
	case "$$yn" in \
	  [yY]|[yY][eE][sS]) \
	    echo "[info] pruning builder cache..."; \
	    docker builder prune -af || { echo '[error] docker builder prune failed'; exit 1; }; \
	    echo "[info] pruning unused images..."; \
	    docker image prune -a -f || { echo '[error] docker image prune failed'; exit 1; }; \
	    echo "[info] prune complete"; \
	    docker system df; \
	    ;; \
	  *) echo "[info] abort prune"; exit 0 ;; \
	esac

rebuild: check secrets
	@echo "[info] REBUILD (ENV=$(ENV) -> canonical=$(ENV_CANON))"
	@echo "[step] compose config (merged)"
	$(DC_ENV_PREFIX)$(DC) $(COMPOSE_ENV_ARGS) -p $(ENV) $(COMPOSE_FILES) config >/dev/null || { echo '[error] compose config failed'; exit 2; }
	@echo "[step] down --remove-orphans"
	$(MAKE) down ENV=$(ENV)
	@echo "[step] build --pull --no-cache"
	$(DC_ENV_PREFIX)$(DC) $(COMPOSE_ENV_ARGS) -p $(ENV) $(COMPOSE_FILES) build --pull --no-cache
	@echo "[step] up -d"
	$(DC_ENV_PREFIX)$(DC) $(COMPOSE_ENV_ARGS) -p $(ENV) $(COMPOSE_FILES) up -d --force-recreate --remove-orphans
	@echo "[step] health check -> $(HEALTH_URL)"
	@if [ -z "$(HEALTH_URL)" ]; then \
	  echo '[warn] HEALTH_URL not set; skipping health check'; \
	else \
	  if command -v curl >/dev/null 2>&1; then \
	    HTTP_STATUS=$$(curl -s -o /dev/null -w '%{http_code}' -I "$(HEALTH_URL)" || echo 000); \
	    if [ -z "$$HTTP_STATUS" ] || [ "$$HTTP_STATUS" = "000" ]; then \
	      echo '[warn] curl health failed (status $$HTTP_STATUS)'; exit 3; \
	    else \
	      echo "[ok] HTTP $$HTTP_STATUS"; \
	    fi; \
	  elif command -v wget >/dev/null 2>&1; then \
	    wget --spider -S "$(HEALTH_URL)" 2>&1 | grep -E 'HTTP/' || echo '[warn] wget health check inconclusive'; \
	  else \
	    echo '[warn] neither curl nor wget installed; skip health check'; \
	  fi; \
	fi
	@echo "[info] rebuild done"

# Simple restart wrapper
.PHONY: restart
restart:
	$(MAKE) down ENV=$(ENV)
	$(MAKE) up ENV=$(ENV)

.PHONY: health
health:
	@echo "[info] HEALTH CHECK $(HEALTH_URL)"
	@if command -v curl >/dev/null 2>&1; then curl -I "$(HEALTH_URL)"; elif command -v wget >/dev/null 2>&1; then wget --spider -S "$(HEALTH_URL)" 2>&1 | sed -n '1,10p'; else echo 'no curl/wget'; fi

config: check secrets
	$(DC_ENV_PREFIX)$(DC) $(COMPOSE_ENV_ARGS) -p $(ENV) $(COMPOSE_FILES) config

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


	
# デフォルトのリポジトリ
REPO ?= torotorokou/sanbou_app

# -------------------------------------------------------------
# gh-secrets: GitHub Environments へ .env をロード
# -------------------------------------------------------------
gh-secrets:
	@# NOTE: .ONESHELL 有効のため行末バックスラッシュ不要 / 先頭は必ず TAB
	@set +u
	JSON_VAL="$${JSON:-}"; CSV_VAL="$${CSV:-}"; PREFIX_VAL="$${PREFIX:-}"; DRY_VAL="$${DRY:-}"; FILE_VAL="$${FILE:-}";
	DRY_FLAG=""; if [ "$$DRY_VAL" = "1" ]; then DRY_FLAG="--dry-run"; fi
	if [ ! -x ./scripts/gh_env_secrets_sync.sh ]; then echo "[error] scripts/gh_env_secrets_sync.sh が見つからないか実行不可"; exit 2; fi
	if [ -n "$$JSON_VAL" ]; then
	  echo "[info] Apply from JSON ($$JSON_VAL)"
	  ./scripts/gh_env_secrets_sync.sh --repo "$(REPO)" --json "$$JSON_VAL" --prefix "$$PREFIX_VAL" $$DRY_FLAG
	elif [ -n "$$CSV_VAL" ]; then
	  echo "[info] Apply from CSV ($$CSV_VAL)"
	  ./scripts/gh_env_secrets_sync.sh --repo "$(REPO)" --csv "$$CSV_VAL" --prefix "$$PREFIX_VAL" $$DRY_FLAG
	else
	  COMMON_FILE="env/.env.common"; SPEC_FILE="env/.env.$(ENV)"
	  if [ -n "$$FILE_VAL" ]; then
	    if [ ! -f "$$FILE_VAL" ]; then echo "[error] $$FILE_VAL not found"; exit 2; fi
	    echo "[info] Apply single env ($(ENV)) from $$FILE_VAL"
	    ./scripts/gh_env_secrets_sync.sh --repo "$(REPO)" --env "$(ENV)" --file "$$FILE_VAL" --prefix "$$PREFIX_VAL" $$DRY_FLAG
	  else
	    if [ ! -f "$$COMMON_FILE" ]; then echo "[error] $$COMMON_FILE not found"; exit 2; fi
	    echo "[info] Apply common: $$COMMON_FILE -> environment '$(ENV)'"
	    ./scripts/gh_env_secrets_sync.sh --repo "$(REPO)" --env "$(ENV)" --file "$$COMMON_FILE" --prefix "$$PREFIX_VAL" $$DRY_FLAG
	    if [ ! -f "$$SPEC_FILE" ]; then echo "[error] $$SPEC_FILE not found"; exit 2; fi
	    echo "[info] Apply specific: $$SPEC_FILE -> environment '$(ENV)'"
	    ./scripts/gh_env_secrets_sync.sh --repo "$(REPO)" --env "$(ENV)" --file "$$SPEC_FILE" --prefix "$$PREFIX_VAL" $$DRY_FLAG
	  fi
	fi

.PHONY: gh-secrets-all
# gh-secrets-all: 全環境まとめ適用
# 可変: DRY=1 (デフォルト 1) を外す/0 にすると実際に書き込み
# 例: make gh-secrets-all DRY=1  /  make gh-secrets-all DRY=0
gh-secrets-all:
	: "DRY=$(DRY) (1=dry-run)"; \
	DRY_VAL=$${DRY:-1}; \
	$(MAKE) gh-secrets ENV=local_dev PREFIX=DEV_ DRY=$$DRY_VAL; \
	$(MAKE) gh-secrets ENV=local_stg PREFIX=STG_ DRY=$$DRY_VAL; \
	$(MAKE) gh-secrets ENV=vm_stg PREFIX=STG_ DRY=$$DRY_VAL; \
	$(MAKE) gh-secrets ENV=vm_prod PREFIX=PROD_ DRY=$$DRY_VAL