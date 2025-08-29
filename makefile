# ===== ultra-simple Makefile (interactive secrets, fixed, with leveled logs) =====
# 使い方:
#   make up            # dev環境（デフォルト）
#   make down          # dev環境を停止（デフォルト）
#   make rebuild       # dev環境で再ビルド
#   make up ENV=stg    # ステージング環境（初回のみキー入力→ secrets/.env.stg.secrets に保存）
#   make up ENV=prod   # 本番環境
#   make down ENV=stg / make logs ENV=prod / make rebuild ENV=stg など
#   追加: DEBUG=1 を付けると [debug] ログを表示
#
# 例:
#   make up                  # dev
#   make rebuild             # dev
#   make up ENV=stg DEBUG=1  # ステージングでデバッグ出力付き

SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c

# --------- 設定項目 ----------
ENV ?= dev                   # デフォルトは dev（stg/prod の場合のみ ENV=xxx を明示）
DEBUG ?= 0                   # 1で[debug]を表示
REMOTE_PULL ?= 0             # 1=リモートレジストリからの pull を試行（認証設定済み時）。0=完全ローカルビルド
# ↑ 行末に多数の空白があるため、その空白が値として取り込まれ [[ -f ]] で存在判定失敗していた。
# GNU make では代入行で # の手前のスペースも値に含まれ得るケースがあるため明示的に strip。
ENV := $(strip $(ENV))
DEBUG := $(strip $(DEBUG))
REMOTE_PULL := $(strip $(REMOTE_PULL))
DC := docker compose
BASE := docker-compose.yml
OVERRIDE := docker-compose.override.yml
EDGE := edge                 # (legacy) 未使用

ENV_FILE := $(strip env/.env.$(ENV))
SECRETS_FILE := $(strip secrets/.env.$(ENV).secrets) # stg/prod の秘密保存先（git ignore想定）
GCP_SA_FILE ?= secrets/gcs-key.json # dev 用デフォルト
# stg/prod は docker-compose.yml の secrets 記述と合わせた個別ファイル名に統一
ifneq ($(ENV),dev)
	GCP_SA_FILE := secrets/gcs-key.$(ENV).json
endif
GCP_SA_FILE := $(strip $(GCP_SA_FILE))

# docker compose の変数展開で ${ENV_FILE} を参照させるため export
export ENV_FILE
export FRONTEND_PORT
export AI_API_PORT
export LEDGER_API_PORT
export SQL_API_PORT
export RAG_API_PORT

# dev は override を使い、stg/prod は base のみ＋profile=edge
FILES := -f $(BASE)
PROFILE :=
ifeq ($(ENV),dev)
  FILES := -f $(BASE) -f $(OVERRIDE)
else ifeq ($(ENV),stg)
	PROFILE := --profile stg
else ifeq ($(ENV),prod)
	PROFILE := --profile prod
else
	$(error ENV は dev / stg / prod のいずれか)
endif

# --------- ログマクロ ----------
define LOG_INFO
	@echo "[info] $(1)"
endef

define LOG_WARN
	@echo "[warn] $(1)"
endef

define LOG_DEBUG
	@if [[ "$(DEBUG)" == "1" ]]; then echo "[debug] $(1)"; fi
endef

define LOG_ERROR_EXIT
	@echo "[error] $(1)"; exit 1
endef

# --------- 便利マクロ ----------
define RUN
	@echo "[info] $(1)"
	$(2)
endef

.PHONY: up down logs ps rebuild config

up:
	$(call LOG_INFO,Start 'up' (ENV=$(ENV)) )
	$(call LOG_DEBUG,ENV_FILE=$(ENV_FILE) SECRETS_FILE=$(SECRETS_FILE) GCP_SA_FILE=$(GCP_SA_FILE))
	$(call LOG_DEBUG,FILES="$(FILES)" PROFILE="$(PROFILE)")

	if [[ ! -f "$(ENV_FILE)" ]]; then
	  $(call LOG_ERROR_EXIT,$(ENV_FILE) がありません)
	fi

	mkdir -p secrets
	if [[ -f "secret/gcs-key.json" && ! -f "$(GCP_SA_FILE)" ]]; then
	  mv -f secret/gcs-key.json "$(GCP_SA_FILE)"
	  $(call LOG_WARN,Migrated legacy 'secret/gcs-key.json' -> '$(GCP_SA_FILE)')
	fi

	if [[ "$(ENV)" == "dev" ]]; then
	  if [[ ! -f "$(GCP_SA_FILE)" ]]; then
	    $(call LOG_WARN,$(GCP_SA_FILE) が見つかりません（GCP を使わない場合は無視可）)
	  fi
	else
	  # stg では prod-* コンテナも起動するため prod 用キーも確保
	  if [[ "$(ENV)" == "stg" ]]; then
	    if [[ -f secrets/gcs-key.json && ! -f secrets/gcs-key.prod.json ]]; then
	      cp secrets/gcs-key.json secrets/gcs-key.prod.json
	      $(call LOG_WARN,Created secrets/gcs-key.prod.json from generic secrets/gcs-key.json)
	    elif [[ -f secrets/gcs-key.stg.json && ! -f secrets/gcs-key.prod.json ]]; then
	      cp secrets/gcs-key.stg.json secrets/gcs-key.prod.json
	      $(call LOG_WARN,Duplicated stg key -> secrets/gcs-key.prod.json)
	    fi
	  fi
	  # 汎用 gcs-key.json だけ存在する場合は環境別ファイルへ複製
	  if [[ -f secrets/gcs-key.json && ! -f "$(GCP_SA_FILE)" ]]; then
	    cp secrets/gcs-key.json "$(GCP_SA_FILE)"
	    $(call LOG_WARN,Created $(GCP_SA_FILE) from generic secrets/gcs-key.json )
	  fi
	  [[ -f "$(SECRETS_FILE)" ]] || { touch "$(SECRETS_FILE)"; chmod 600 "$(SECRETS_FILE)"; }

	  if [[ -f "secrets/.env.$(ENV).secrets " && ! -f "$(SECRETS_FILE)" ]]; then
	    mv -f "secrets/.env.$(ENV).secrets " "$(SECRETS_FILE)"
	    $(call LOG_WARN,Renamed 'secrets/.env.$(ENV).secrets ' -> '$(SECRETS_FILE)')
	  fi
	  if [[ -f "secrets/gcs-key.json " && ! -f "$(GCP_SA_FILE)" ]]; then
	    mv -f "secrets/gcs-key.json " "$(GCP_SA_FILE)"
	    $(call LOG_WARN,Renamed 'secrets/gcs-key.json ' -> '$(GCP_SA_FILE)')
	  fi

	  set +e; set -a; . "$(SECRETS_FILE)" 2>/dev/null; set +a; set -e

	  if [[ -z "${OPENAI_API_KEY:-}" ]]; then
	    read -rsp "Enter OPENAI_API_KEY (hidden): " OPENAI_API_KEY; echo
	    printf 'OPENAI_API_KEY=%s\n' "$$OPENAI_API_KEY" >> "$(SECRETS_FILE)"
	    $(call LOG_INFO,OPENAI_API_KEY saved to $(SECRETS_FILE))
	  fi
	  if [[ -z "${GEMINI_API_KEY:-}" ]]; then
	    read -rsp "Enter GEMINI_API_KEY (hidden): " GEMINI_API_KEY; echo
	    printf 'GEMINI_API_KEY=%s\n' "$$GEMINI_API_KEY" >> "$(SECRETS_FILE)"
	    $(call LOG_INFO,GEMINI_API_KEY saved to $(SECRETS_FILE))
	  fi

	  set -a; . "$(SECRETS_FILE)"; set +a

	  if [[ ! -f "$(GCP_SA_FILE)" ]]; then
	    $(call LOG_ERROR_EXIT,$(GCP_SA_FILE) not found)
	  fi

	  $(call RUN,compose pull,$(DC) --env-file "$(ENV_FILE)" -p $(ENV) $(PROFILE) $(FILES) pull || true)

	  if [[ "$(REMOTE_PULL)" == "1" ]]; then
	    $(call RUN,compose pull,$(DC) --env-file "$(ENV_FILE)" -p $(ENV) $(PROFILE) $(FILES) pull || true)
	  else
	    echo "[info] REMOTE_PULL=0: remote pull をスキップ (compose build でローカル生成)"
	  fi
	fi

	$(DC) --env-file "$(ENV_FILE)" -p $(ENV) $(PROFILE) $(FILES) up -d --build --remove-orphans
	$(call LOG_INFO,Finished 'up' successfully)

down:
	$(call LOG_INFO,Stop containers (ENV=$(ENV)))
	$(call RUN,compose down,$(DC) -p $(ENV) down --remove-orphans)
	$(call LOG_INFO,Finished 'down' successfully)

logs:
	$(call LOG_INFO,Attaching logs -f (CTRL+Cで離脱))
	$(DC) -p $(ENV) logs -f

ps:
	$(call RUN,compose ps,$(DC) -p $(ENV) ps)

rebuild:
	$(call LOG_INFO,Start 'rebuild' (ENV=$(ENV)) )
	$(call LOG_DEBUG,ENV_FILE=$(ENV_FILE) SECRETS_FILE=$(SECRETS_FILE) GCP_SA_FILE=$(GCP_SA_FILE))
	$(call LOG_DEBUG,FILES="$(FILES)" PROFILE="$(PROFILE)")

	# 先に既存コンテナを停止 (ポート競合防止)
	$(call LOG_INFO,Pre-clean existing project containers: down --remove-orphans)
	$(DC) -p $(ENV) down --remove-orphans || true
	# (一時無効化) 明示的 container_name 競合対策ループ
	# @containers="prod-frontend prod-ai_api prod-ledger_api prod-sql_api prod-rag_api prod-db stg-frontend stg-ai_api stg-ledger_api stg-sql_api stg-rag_api stg-db edge-nginx"; for c in $$containers; do if docker ps -a --format '{{.Names}}' | grep -q "^$$c$"; then echo "[info] Force removing stale container: $$c"; docker rm -f $$c >/dev/null 2>&1 || true; fi; done
	# シンプル強制削除（存在しなくても無視）
	@docker rm -f prod-frontend prod-ai_api prod-ledger_api prod-sql_api prod-rag_api prod-db stg-frontend stg-ai_api stg-ledger_api stg-sql_api stg-rag_api stg-db edge-nginx >/dev/null 2>&1 || true

	# 過去に project name 未指定で生成された dev-* などのレガシー名称コンテナを掃除 (任意)
	@if [[ "$(ENV)" == "dev" ]]; then \
	  legacy=$$(docker ps -a --format '{{.Names}}' | grep -E '^(dev|sanbou_app)-(ai_api|ledger_api|sql_api|rag_api|frontend)-' || true); \
	  if [[ -n "$$legacy" ]]; then \
	    echo "[info] Removing legacy containers: $$legacy"; \
	    docker rm -f $$legacy >/dev/null 2>&1 || true; \
	  fi; \
	fi

	if [[ ! -f "$(ENV_FILE)" ]]; then
	  $(call LOG_ERROR_EXIT,$(ENV_FILE) がありません)
	fi

	mkdir -p secrets
	if [[ -f "secret/gcs-key.json" && ! -f "$(GCP_SA_FILE)" ]]; then
	  mv -f secret/gcs-key.json "$(GCP_SA_FILE)"
	  $(call LOG_WARN,Migrated legacy 'secret/gcs-key.json' -> '$(GCP_SA_FILE)')
	fi

	if [[ "$(ENV)" != "dev" ]]; then
	  if [[ -f "secrets/.env.$(ENV).secrets " && ! -f "$(SECRETS_FILE)" ]]; then
	    mv -f "secrets/.env.$(ENV).secrets " "$(SECRETS_FILE)"
	    $(call LOG_WARN,Renamed 'secrets/.env.$(ENV).secrets ' -> '$(SECRETS_FILE)')
	  fi
	  if [[ -f "secrets/gcs-key.json " && ! -f "$(GCP_SA_FILE)" ]]; then
	    mv -f "secrets/gcs-key.json " "$(GCP_SA_FILE)"
	    $(call LOG_WARN,Renamed 'secrets/gcs-key.json ' -> '$(GCP_SA_FILE)')
	  fi
	  if [[ "$(ENV)" == "stg" ]]; then
	    if [[ -f secrets/gcs-key.json && ! -f secrets/gcs-key.prod.json ]]; then
	      cp secrets/gcs-key.json secrets/gcs-key.prod.json
	      $(call LOG_WARN,Created secrets/gcs-key.prod.json from generic secrets/gcs-key.json)
	    elif [[ -f secrets/gcs-key.stg.json && ! -f secrets/gcs-key.prod.json ]]; then
	      cp secrets/gcs-key.stg.json secrets/gcs-key.prod.json
	      $(call LOG_WARN,Duplicated stg key -> secrets/gcs-key.prod.json)
	    fi
	  fi
	  # 汎用 gcs-key.json しか無い場合の複製
	  if [[ -f secrets/gcs-key.json && ! -f "$(GCP_SA_FILE)" ]]; then
	    cp secrets/gcs-key.json "$(GCP_SA_FILE)"
	    $(call LOG_WARN,Created $(GCP_SA_FILE) from generic secrets/gcs-key.json )
	  fi
	  if [[ ! -f "$(SECRETS_FILE)" ]]; then
	    $(call LOG_ERROR_EXIT,secrets 未設定。先に 'make up ENV=$(ENV)' で設定してください。)
	  fi
	  set -a; . "$(SECRETS_FILE)"; set +a

	  if [[ ! -f "$(GCP_SA_FILE)" ]]; then
	    $(call LOG_ERROR_EXIT,$(GCP_SA_FILE) not found)
	  fi

	  if [[ "$(REMOTE_PULL)" == "1" ]]; then
	    $(call RUN,compose pull,$(DC) --env-file "$(ENV_FILE)" -p $(ENV) $(PROFILE) $(FILES) pull || true)
	  else
	    echo "[info] REMOTE_PULL=0: remote pull をスキップ (build のみ)"
	  fi
	else
	  if [[ ! -f "$(GCP_SA_FILE)" ]]; then
	    $(call LOG_WARN,$(GCP_SA_FILE) が見つかりません（GCP を使わない場合は無視可）)
	  fi
	fi

	$(DC) --env-file "$(ENV_FILE)" -p $(ENV) $(PROFILE) $(FILES) build --no-cache
	$(DC) --env-file "$(ENV_FILE)" -p $(ENV) $(PROFILE) $(FILES) up -d --force-recreate --remove-orphans
	$(call LOG_INFO,Finished 'rebuild' successfully)

config:
	$(call RUN,compose config,$(DC) --env-file "$(ENV_FILE)" -p $(ENV) $(PROFILE) $(FILES) config)
