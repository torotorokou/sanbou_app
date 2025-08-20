# ===== ultra-simple Makefile (interactive secrets, fixed, with leveled logs) =====
# 使い方:
#   make up ENV=dev
#   make up ENV=stg     # 初回のみキー入力（非表示）→ secrets/.env.stg.secrets に保存
#   make up ENV=prod
#   make down ENV=stg / make logs ENV=prod / make rebuild ENV=stg など
#   追加: DEBUG=1 を付けると [debug] ログを表示
#
# 例:
#   make rebuild ENV=dev
#   make up ENV=stg DEBUG=1

SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c

# --------- 設定項目 ----------
ENV ?= dev                   # dev / stg / prod
DEBUG ?= 0                   # 1で[debug]を表示
DC := docker compose
BASE := docker-compose.yml
OVERRIDE := docker-compose.override.yml
EDGE := edge                 # Nginx を起動する profile 名（stg/prod 用）

ENV_FILE := env/.env.$(ENV)
SECRETS_FILE := $(strip secrets/.env.$(ENV).secrets) # stg/prod の秘密保存先（git ignore想定）
GCP_SA_FILE ?= secrets/gcp-sa.json # 必要なら存在チェック
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
else
  PROFILE := --profile $(EDGE)
endif

# --------- ログマクロ ----------
# 使い方: $(call LOG_INFO,Message)
define LOG_INFO
	@echo "[info] $(1)"
endef

define LOG_WARN
	@echo "[warn] $(1)"
endef

define LOG_DEBUG
	@if [[ "$(DEBUG)" == "1" ]]; then echo "[debug] $(1)"; fi
endef

# エラーはメッセージを出して終了
define LOG_ERROR_EXIT
	@echo "[error] $(1)"; exit 1
endef

# --------- 便利マクロ ----------
# コマンド実行前後で情報を出すヘルパ（エラー時はそのまま落ちる）
# 使い方: $(call RUN,説明文,実コマンド)
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

	# --- migrate legacy path: secret/gcs-key.json -> secrets/gcp-sa.json ---
	mkdir -p secrets
	if [[ -f "secret/gcs-key.json" && ! -f "$(GCP_SA_FILE)" ]]; then
	  mv -f secret/gcs-key.json "$(GCP_SA_FILE)"
	  $(call LOG_WARN,Migrated legacy 'secret/gcs-key.json' -> '$(GCP_SA_FILE)')
	fi

	# --- dev: GCP SA の簡易用意 ---
	if [[ "$(ENV)" == "dev" ]]; then
	  if [[ ! -f "$(GCP_SA_FILE)" ]]; then
	    $(call LOG_WARN,$(GCP_SA_FILE) が見つかりません（GCP を使わない場合は無視可）)
	  fi

	# --- stg/prod: 秘密を対話取得→保存→読み込み ---
	else
	  [[ -f "$(SECRETS_FILE)" ]] || { touch "$(SECRETS_FILE)"; chmod 600 "$(SECRETS_FILE)"; }

	  # 末尾スペース付き誤ファイルが存在する場合は自動修正
	  if [[ -f "secrets/.env.$(ENV).secrets " && ! -f "$(SECRETS_FILE)" ]]; then
	    mv -f "secrets/.env.$(ENV).secrets " "$(SECRETS_FILE)"
	    $(call LOG_WARN,Renamed 'secrets/.env.$(ENV).secrets ' -> '$(SECRETS_FILE)')
	  fi
	  if [[ -f "secrets/gcp-sa.json " && ! -f "$(GCP_SA_FILE)" ]]; then
	    mv -f "secrets/gcp-sa.json " "$(GCP_SA_FILE)"
	    $(call LOG_WARN,Renamed 'secrets/gcp-sa.json ' -> '$(GCP_SA_FILE)')
	  fi

	  # 既存の秘密を読み込み（あれば；未設定でもエラーにしない）
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

	  # このシェルに export
	  set -a; . "$(SECRETS_FILE)"; set +a

	  # 必要なら GCP SA JSON の存在チェック
	  if [[ ! -f "$(GCP_SA_FILE)" ]]; then
	    $(call LOG_ERROR_EXIT,$(GCP_SA_FILE) not found)
	  fi

	  # stg/prod はタグ更新を取り込むため pull を実行（定義が無い場合は無視）
	  $(call RUN,compose pull,$(DC) --env-file "$(ENV_FILE)" -p $(ENV) $(PROFILE) $(FILES) pull || true)
	fi

	$(call RUN,compose up,$(DC) --env-file "$(ENV_FILE)" -p $(ENV) $(PROFILE) $(FILES) up -d --remove-orphans)
	$(call LOG_INFO,Finished 'up' successfully)

down:
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

	if [[ ! -f "$(ENV_FILE)" ]]; then
	  $(call LOG_ERROR_EXIT,$(ENV_FILE) がありません)
	fi

	# --- migrate legacy path: secret/gcs-key.json -> secrets/gcp-sa.json ---
	mkdir -p secrets
	if [[ -f "secret/gcs-key.json" && ! -f "$(GCP_SA_FILE)" ]]; then
	  mv -f secret/gcs-key.json "$(GCP_SA_FILE)"
	  $(call LOG_WARN,Migrated legacy 'secret/gcs-key.json' -> '$(GCP_SA_FILE)')
	fi

	# stg/prod は secrets と SA を確認してから再作成
	if [[ "$(ENV)" != "dev" ]]; then
	  # 末尾スペース付き誤ファイルが存在する場合は自動修正
	  if [[ -f "secrets/.env.$(ENV).secrets " && ! -f "$(SECRETS_FILE)" ]]; then
	    mv -f "secrets/.env.$(ENV).secrets " "$(SECRETS_FILE)"
	    $(call LOG_WARN,Renamed 'secrets/.env.$(ENV).secrets ' -> '$(SECRETS_FILE)')
	  fi
	  if [[ -f "secrets/gcp-sa.json " && ! -f "$(GCP_SA_FILE)" ]]; then
	    mv -f "secrets/gcp-sa.json " "$(GCP_SA_FILE)"
	    $(call LOG_WARN,Renamed 'secrets/gcp-sa.json ' -> '$(GCP_SA_FILE)')
	  fi
	  if [[ ! -f "$(SECRETS_FILE)" ]]; then
	    $(call LOG_ERROR_EXIT,secrets 未設定。先に 'make up ENV=$(ENV)' で設定してください。)
	  fi
	  set -a; . "$(SECRETS_FILE)"; set +a

	  if [[ ! -f "$(GCP_SA_FILE)" ]]; then
	    $(call LOG_ERROR_EXIT,$(GCP_SA_FILE) not found)
	  fi

	  $(call RUN,compose pull,$(DC) --env-file "$(ENV_FILE)" -p $(ENV) $(PROFILE) $(FILES) pull || true)
	fi

	# dev 環境: SA の簡易用意（up と同等）
	if [[ "$(ENV)" == "dev" ]]; then
	  if [[ ! -f "$(GCP_SA_FILE)" ]]; then
	    $(call LOG_WARN,$(GCP_SA_FILE) が見つかりません（GCP を使わない場合は無視可）)
	  fi
	fi

	$(call RUN,compose build --no-cache,$(DC) --env-file "$(ENV_FILE)" -p $(ENV) $(PROFILE) $(FILES) build --no-cache)
	$(call RUN,compose up -d --force-recreate,$(DC) --env-file "$(ENV_FILE)" -p $(ENV) $(PROFILE) $(FILES) up -d --force-recreate --remove-orphans)
	$(call LOG_INFO,Finished 'rebuild' successfully)

config:
	$(call RUN,compose config,$(DC) --env-file "$(ENV_FILE)" -p $(ENV) $(PROFILE) $(FILES) config)
