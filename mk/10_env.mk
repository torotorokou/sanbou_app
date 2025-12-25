## =============================================================
## mk/10_env.mk - Environment mapping and configuration
## =============================================================
##
## ENV に応じて:
##   - 使用する docker-compose.yml
##   - 使用する .env ファイル
##   - health check URL
##   - build 有無
##
## ★ nginx 動作確認（HTTP リダイレクト修正後の確認手順）:
##
##   【vm_stg での確認】
##   VM 内で:
##     curl -I http://localhost/health    # → HTTP/1.1 200 OK
##     curl -I http://localhost/          # → HTTP/1.1 200 OK, Content-Type: text/html
##                                        #    ※ Location: https://... が含まれないこと
##   ローカル PC から (Tailscale 経由):
##     http://100.119.243.45/             # → React 画面が表示され、https へのリダイレクトなし
##
##   【vm_prod での確認】
##   VM 内で:
##     curl -I http://localhost/health    # → HTTP/1.1 200 OK
##     curl -I http://localhost/          # → HTTP/1.1 200 OK, Content-Type: text/html
##                                        #    ※ Location: https://localhost/ が含まれないこと
##   GCP LB + IAP 経由:
##     https://sanbou-app.jp/             # → React 画面が表示されること
##                                        #    ※ HTTPS は LB 側で終端、VM は HTTP(80) のみ
## =============================================================

## グローバル環境変数
## -------------------------------------------------------------
ENV ?= local_dev
ENV := $(strip $(ENV))
DC  := docker compose
BUILDKIT ?= 1
PROGRESS ?= plain

ENV_CANON := $(ENV)

# 後方互換性のための警告と自動変換
ifeq ($(ENV),dev)
	$(warning [compat] ENV=dev は非推奨です。ENV=local_dev を使用してください)
	ENV_CANON := local_dev
endif
ifeq ($(ENV),stg)
	$(warning [compat] ENV=stg は非推奨です。ENV=vm_stg を使用してください)
	ENV_CANON := vm_stg
endif
ifeq ($(ENV),prod)
	$(warning [compat] ENV=prod は非推奨です。ENV=vm_prod を使用してください)
	ENV_CANON := vm_prod
endif
# local_stg / local_prod は廃止済み
ifeq ($(ENV),local_stg)
	$(error ENV=local_stg は廃止されました。ENV=vm_stg を使用してください)
endif
ifeq ($(ENV),local_prod)
	$(error ENV=local_prod は廃止されました。ENV=vm_prod を使用してください)
endif

# 共通 .env は常にこれ
ENV_FILE_COMMON := env/.env.common
# ENV 個別（後で ENV_CANON によって上書き）
ENV_FILE        := env/.env.$(ENV)

# ENV ごとの compose / env / health
ifeq ($(ENV_CANON),local_dev)
	ENV_FILE      := env/.env.local_dev
	COMPOSE_FILES := -f docker/docker-compose.dev.yml
	HEALTH_URL    := http://localhost:8001/health
else ifeq ($(ENV_CANON),vm_stg)
	ENV_FILE      := env/.env.vm_stg
	COMPOSE_FILES := -f docker/docker-compose.stg.yml
	HEALTH_URL    := http://100.64.0.1/health
else ifeq ($(ENV_CANON),vm_prod)
	ENV_FILE      := env/.env.vm_prod
	COMPOSE_FILES := -f docker/docker-compose.prod.yml
	HEALTH_URL    := https://sanbou-app.jp/health
else ifeq ($(ENV_CANON),local_demo)
	ENV_FILE      := env/.env.local_demo
	COMPOSE_FILES := -f docker/docker-compose.local_demo.yml
	HEALTH_URL    := http://localhost:8013/health
else
	$(error Unsupported ENV: $(ENV). Supported: local_dev, vm_stg, vm_prod, local_demo)
endif

# vm_stg / vm_prod は Artifact Registry からイメージ pull のみ (--build なし)
ifeq ($(ENV_CANON),vm_stg)
	UP_BUILD_FLAGS :=
else ifeq ($(ENV_CANON),vm_prod)
	UP_BUILD_FLAGS :=
else
	UP_BUILD_FLAGS := --build
endif

SECRETS_FILE      := secrets/.env.$(ENV).secrets
# secrets ファイルは存在する場合のみ --env-file に載せる
COMPOSE_ENV_ARGS  := --env-file $(ENV_FILE_COMMON) --env-file $(ENV_FILE) \
                     $(if $(wildcard $(SECRETS_FILE)),--env-file $(SECRETS_FILE),)
COMPOSE_FILE_LIST := $(strip $(subst -f ,,$(COMPOSE_FILES)))
DC_FULL           := $(DC) $(COMPOSE_ENV_ARGS) -p $(ENV) $(COMPOSE_FILES)
