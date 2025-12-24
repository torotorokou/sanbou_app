## ============================================================
## Artifact Registry 設定 (STG / PROD 共通)
##   - ローカルPCで build / push するための設定
##   - STG: --target stg でビルド
##   - PROD: --target prod でビルド
## ============================================================

##@ Registry

# STG 設定
STG_REGION         ?= asia-northeast1
STG_PROJECT_ID     ?= honest-sanbou-app-stg
STG_ARTIFACT_REPO  ?= sanbou-app
STG_IMAGE_REGISTRY := $(STG_REGION)-docker.pkg.dev/$(STG_PROJECT_ID)/$(STG_ARTIFACT_REPO)
STG_IMAGE_TAG      ?= stg-latest
# 後方互換: 昔のドキュメントで IMAGE_TAG を使っている場合に対応（STG 側）
ifdef IMAGE_TAG
  STG_IMAGE_TAG := $(IMAGE_TAG)
endif

# PROD 設定
PROD_REGION         ?= asia-northeast1
PROD_PROJECT_ID     ?= honest-sanbou-app-prod
PROD_ARTIFACT_REPO  ?= sanbou-app
PROD_IMAGE_REGISTRY := $(PROD_REGION)-docker.pkg.dev/$(PROD_PROJECT_ID)/$(PROD_ARTIFACT_REPO)
PROD_IMAGE_TAG      ?= prod-latest
# 後方互換: IMAGE_TAG を指定したら PROD 側にも反映（必要に応じて使う）
ifdef IMAGE_TAG
  PROD_IMAGE_TAG := $(IMAGE_TAG)
endif

## STG → PROD 昇格用タグ（デフォルトは stg-latest → prod-latest）
PROMOTE_SRC_TAG ?= stg-latest
PROMOTE_DST_TAG ?= prod-latest

## ------------------------------------------------------------
## gcloud 認証（STG / PROD 共通）
##   - 一度だけ実行しておけば OK
##   - gcloud auth login / config set project は事前に実施しておくこと
## ------------------------------------------------------------
.PHONY: gcloud-auth-docker
gcloud-auth-docker: ## Authenticate Docker with Artifact Registry (STG + PROD)
	@gcloud auth configure-docker $(STG_REGION)-docker.pkg.dev
	@gcloud auth configure-docker $(PROD_REGION)-docker.pkg.dev

## ============================================================
## STG 用 Docker イメージ build & push
##  - ローカルPCで実行する前提
##  - VM (vm_stg) では build せず pull + up だけ
##  - 使い方:
##      make publish-stg-images STG_IMAGE_TAG=stg-20251208
##      NO_CACHE=1 PULL=1 make publish-stg-images STG_IMAGE_TAG=stg-20251208
## ============================================================
.PHONY: build-stg-images push-stg-images publish-stg-images

build-stg-images: ## Build STG images (STG_IMAGE_TAG=xxx, NO_CACHE=1, PULL=1)
	@echo ">>> Build STG images (tag=$(STG_IMAGE_TAG), target=stg)"
	docker build $(BUILD_PULL_FLAG) $(BUILD_NO_CACHE_FLAG) \
	  -t $(STG_IMAGE_REGISTRY)/core_api:$(STG_IMAGE_TAG) \
	  -f app/backend/core_api/Dockerfile --target stg app/backend
	docker build $(BUILD_PULL_FLAG) $(BUILD_NO_CACHE_FLAG) \
	  -t $(STG_IMAGE_REGISTRY)/plan_worker:$(STG_IMAGE_TAG) \
	  -f app/backend/plan_worker/Dockerfile --target stg app/backend
	docker build $(BUILD_PULL_FLAG) $(BUILD_NO_CACHE_FLAG) \
	  -t $(STG_IMAGE_REGISTRY)/ai_api:$(STG_IMAGE_TAG) \
	  -f app/backend/ai_api/Dockerfile --target stg app/backend
	docker build $(BUILD_PULL_FLAG) $(BUILD_NO_CACHE_FLAG) \
	  -t $(STG_IMAGE_REGISTRY)/ledger_api:$(STG_IMAGE_TAG) \
	  -f app/backend/ledger_api/Dockerfile --target stg app/backend
	docker build $(BUILD_PULL_FLAG) $(BUILD_NO_CACHE_FLAG) \
	  -t $(STG_IMAGE_REGISTRY)/rag_api:$(STG_IMAGE_TAG) \
	  -f app/backend/rag_api/Dockerfile --target stg app/backend
	docker build $(BUILD_PULL_FLAG) $(BUILD_NO_CACHE_FLAG) \
	  -t $(STG_IMAGE_REGISTRY)/manual_api:$(STG_IMAGE_TAG) \
	  -f app/backend/manual_api/Dockerfile --target stg app/backend
	docker build $(BUILD_PULL_FLAG) $(BUILD_NO_CACHE_FLAG) \
	  -t $(STG_IMAGE_REGISTRY)/nginx:$(STG_IMAGE_TAG) \
	  -f app/frontend/Dockerfile --target stg app/frontend

push-stg-images: ## Push STG images to Artifact Registry (STG_IMAGE_TAG=xxx)
	@echo ">>> Push STG images (tag=$(STG_IMAGE_TAG))"
	@for svc in core_api plan_worker ai_api ledger_api rag_api manual_api nginx; do \
	  echo "  -> push $(STG_IMAGE_REGISTRY)/$$svc:$(STG_IMAGE_TAG)"; \
	  docker push $(STG_IMAGE_REGISTRY)/$$svc:$(STG_IMAGE_TAG); \
	done

publish-stg-images: build-stg-images push-stg-images ## Build and push STG images (STG_IMAGE_TAG=xxx)
	@echo "[ok] STG images built & pushed (tag=$(STG_IMAGE_TAG))"

## ============================================================
## PROD 用 Docker イメージ build & push
##  - ローカルPCで実行する前提
##  - VM (vm_prod) では build せず pull + up だけ
##  - 使い方:
##      make publish-prod-images PROD_IMAGE_TAG=prod-20251209
##      NO_CACHE=1 PULL=1 make publish-prod-images PROD_IMAGE_TAG=prod-20251209
## ============================================================
.PHONY: build-prod-images push-prod-images publish-prod-images

build-prod-images: ## Build PROD images (PROD_IMAGE_TAG=xxx, NO_CACHE=1, PULL=1)
	@echo ">>> Build PROD images (tag=$(PROD_IMAGE_TAG), target=prod)"
	docker build $(BUILD_PULL_FLAG) $(BUILD_NO_CACHE_FLAG) \
	  -t $(PROD_IMAGE_REGISTRY)/core_api:$(PROD_IMAGE_TAG) \
	  -f app/backend/core_api/Dockerfile --target prod app/backend
	docker build $(BUILD_PULL_FLAG) $(BUILD_NO_CACHE_FLAG) \
	  -t $(PROD_IMAGE_REGISTRY)/plan_worker:$(PROD_IMAGE_TAG) \
	  -f app/backend/plan_worker/Dockerfile --target prod app/backend
	docker build $(BUILD_PULL_FLAG) $(BUILD_NO_CACHE_FLAG) \
	  -t $(PROD_IMAGE_REGISTRY)/ai_api:$(PROD_IMAGE_TAG) \
	  -f app/backend/ai_api/Dockerfile --target prod app/backend
	docker build $(BUILD_PULL_FLAG) $(BUILD_NO_CACHE_FLAG) \
	  -t $(PROD_IMAGE_REGISTRY)/ledger_api:$(PROD_IMAGE_TAG) \
	  -f app/backend/ledger_api/Dockerfile --target prod app/backend
	docker build $(BUILD_PULL_FLAG) $(BUILD_NO_CACHE_FLAG) \
	  -t $(PROD_IMAGE_REGISTRY)/rag_api:$(PROD_IMAGE_TAG) \
	  -f app/backend/rag_api/Dockerfile --target prod app/backend
	docker build $(BUILD_PULL_FLAG) $(BUILD_NO_CACHE_FLAG) \
	  -t $(PROD_IMAGE_REGISTRY)/manual_api:$(PROD_IMAGE_TAG) \
	  -f app/backend/manual_api/Dockerfile --target prod app/backend
	docker build $(BUILD_PULL_FLAG) $(BUILD_NO_CACHE_FLAG) \
	  -t $(PROD_IMAGE_REGISTRY)/nginx:$(PROD_IMAGE_TAG) \
	  -f app/frontend/Dockerfile --target prod app/frontend

push-prod-images: ## Push PROD images to Artifact Registry (PROD_IMAGE_TAG=xxx)
	@echo ">>> Push PROD images (tag=$(PROD_IMAGE_TAG))"
	@for svc in core_api plan_worker ai_api ledger_api rag_api manual_api nginx; do \
	  echo "  -> push $(PROD_IMAGE_REGISTRY)/$$svc:$(PROD_IMAGE_TAG)"; \
	  docker push $(PROD_IMAGE_REGISTRY)/$$svc:$(PROD_IMAGE_TAG); \
	done

publish-prod-images: build-prod-images push-prod-images ## Build and push PROD images (PROD_IMAGE_TAG=xxx)
	@echo "[ok] PROD images built & pushed (tag=$(PROD_IMAGE_TAG))"

## ============================================================
## Git ref (tag/commit) から checkout せずに build & push する
##   - git worktree を一時作成して、その中で既存ターゲットを実行
##   - 使い方（例）:
##       NO_CACHE=1 PULL=1 make publish-stg-images-from-ref GIT_REF=v1.2.3
##       NO_CACHE=1 PULL=1 make publish-stg-images-from-ref GIT_REF=3ef33710 STG_IMAGE_TAG=stg-latest
##       NO_CACHE=1 PULL=1 make publish-prod-images-from-ref GIT_REF=v1.2.3
## ============================================================

.PHONY: publish-stg-images-from-ref publish-prod-images-from-ref

# 一時worktreeの親ディレクトリ（必要に応じて変更）
WORKTREE_TMP_BASE ?= /tmp/sanbou_worktree

publish-stg-images-from-ref: ## Build and push STG from git ref without checkout (GIT_REF=v1.2.3)
	@if [ -z "$(GIT_REF)" ]; then \
	  echo "[error] GIT_REF is required. e.g. make $@ GIT_REF=v1.2.3"; \
	  exit 1; \
	fi
	@bash -c 'set -euo pipefail; \
	mkdir -p "$(WORKTREE_TMP_BASE)"; \
	WT_DIR="$$(mktemp -d $(WORKTREE_TMP_BASE)/stg_build_XXXXXX)"; \
	cleanup() { \
	  echo "[info] cleanup worktree $$WT_DIR"; \
	  git -C "$(CURDIR)" worktree remove -f "$$WT_DIR" >/dev/null 2>&1 || true; \
	  rm -rf "$$WT_DIR" >/dev/null 2>&1 || true; \
	}; \
	trap cleanup EXIT; \
	echo "[info] fetch tags..."; \
	git -C "$(CURDIR)" fetch --tags --prune; \
	echo "[info] create worktree: ref=$(GIT_REF) dir=$$WT_DIR"; \
	git -C "$(CURDIR)" worktree add --detach "$$WT_DIR" "$(GIT_REF)"; \
	DEFAULT_TAG="stg-$$(echo "$(GIT_REF)" | tr "/:@" "---")"; \
	TAG_TO_USE="$${STG_IMAGE_TAG:-$$DEFAULT_TAG}"; \
	echo "[info] build&push STG from ref=$(GIT_REF) tag=$$TAG_TO_USE"; \
	( cd "$$WT_DIR" && \
	  NO_CACHE="$(NO_CACHE)" PULL="$(PULL)" \
	  $(MAKE) --no-print-directory publish-stg-images STG_IMAGE_TAG="$$TAG_TO_USE" \
	); \
	echo "[ok] publish-stg-images-from-ref done (ref=$(GIT_REF), tag=$$TAG_TO_USE)"'

publish-prod-images-from-ref: ## Build and push PROD from git ref without checkout (GIT_REF=v1.2.3)
	@if [ -z "$(GIT_REF)" ]; then \
	  echo "[error] GIT_REF is required. e.g. make $@ GIT_REF=v1.2.3"; \
	  exit 1; \
	fi
	@bash -c 'set -euo pipefail; \
	mkdir -p "$(WORKTREE_TMP_BASE)"; \
	WT_DIR="$$(mktemp -d $(WORKTREE_TMP_BASE)/prod_build_XXXXXX)"; \
	cleanup() { \
	  echo "[info] cleanup worktree $$WT_DIR"; \
	  git -C "$(CURDIR)" worktree remove -f "$$WT_DIR" >/dev/null 2>&1 || true; \
	  rm -rf "$$WT_DIR" >/dev/null 2>&1 || true; \
	}; \
	trap cleanup EXIT; \
	echo "[info] fetch tags..."; \
	git -C "$(CURDIR)" fetch --tags --prune; \
	echo "[info] create worktree: ref=$(GIT_REF) dir=$$WT_DIR"; \
	git -C "$(CURDIR)" worktree add --detach "$$WT_DIR" "$(GIT_REF)"; \
	DEFAULT_TAG="prod-$$(echo "$(GIT_REF)" | tr "/:@" "---")"; \
	TAG_TO_USE="$${PROD_IMAGE_TAG:-$$DEFAULT_TAG}"; \
	echo "[info] build&push PROD from ref=$(GIT_REF) tag=$$TAG_TO_USE"; \
	( cd "$$WT_DIR" && \
	  NO_CACHE="$(NO_CACHE)" PULL="$(PULL)" \
	  $(MAKE) --no-print-directory publish-prod-images PROD_IMAGE_TAG="$$TAG_TO_USE" \
	); \
	echo "[ok] publish-prod-images-from-ref done (ref=$(GIT_REF), tag=$$TAG_TO_USE)"'

## ============================================================
## STG → PROD イメージ昇格（別プロジェクト Artifact Registry コピー）
##   使い方:
##     make promote-stg-to-prod PROMOTE_SRC_TAG=stg-20251209 PROMOTE_DST_TAG=prod-20251209
##   実装:
##     docker pull (STG) → docker tag (PROD名) → docker push (PROD)
## ============================================================
.PHONY: promote-stg-to-prod

promote-stg-to-prod: ## Promote STG images to PROD (PROMOTE_SRC_TAG=xxx PROMOTE_DST_TAG=xxx)
	@echo "[info] Promote images from STG to PROD (docker pull/tag/push)"
	@echo "[info]   STG:  $(STG_IMAGE_REGISTRY):$(PROMOTE_SRC_TAG)"
	@echo "[info]   PROD: $(PROD_IMAGE_REGISTRY):$(PROMOTE_DST_TAG)"
	@for svc in core_api plan_worker ai_api ledger_api rag_api manual_api nginx; do \
	  SRC_IMG="$(STG_IMAGE_REGISTRY)/$$svc:$(PROMOTE_SRC_TAG)"; \
	  DST_IMG="$(PROD_IMAGE_REGISTRY)/$$svc:$(PROMOTE_DST_TAG)"; \
	  echo "  -> copy $$svc: $(PROMOTE_SRC_TAG) -> $(PROMOTE_DST_TAG)"; \
	  echo "     SRC=$$SRC_IMG"; \
	  echo "     DST=$$DST_IMG"; \
	  docker pull $$SRC_IMG; \
	  docker tag  $$SRC_IMG $$DST_IMG; \
	  docker push $$DST_IMG; \
	done
	@echo "[ok] promoted STG tag '$(PROMOTE_SRC_TAG)' to PROD tag '$(PROMOTE_DST_TAG)' (via docker)"

## ============================================================
## イメージ存在確認（デバッグ用）
## ============================================================
.PHONY: check-stg-images check-prod-images

check-stg-images: ## Check STG images in Artifact Registry (STG_IMAGE_TAG=xxx)
	@echo "[info] Checking STG images (tag=$(STG_IMAGE_TAG))"
	@for svc in core_api plan_worker ai_api ledger_api rag_api manual_api nginx; do \
	  echo "  -> checking $(STG_IMAGE_REGISTRY)/$$svc:$(STG_IMAGE_TAG)"; \
	  gcloud artifacts docker images list $(STG_REGION)-docker.pkg.dev/$(STG_PROJECT_ID)/$(STG_ARTIFACT_REPO) \
	    --filter="package=$$svc AND tags:$(STG_IMAGE_TAG)" --format="table(package,tags)" || true; \
	done

check-prod-images: ## Check PROD images in Artifact Registry (PROD_IMAGE_TAG=xxx)
	@echo "[info] Checking PROD images (tag=$(PROD_IMAGE_TAG))"
	@for svc in core_api plan_worker ai_api ledger_api rag_api manual_api nginx; do \
	  echo "  -> checking $(PROD_IMAGE_REGISTRY)/$$svc:$(PROD_IMAGE_TAG)"; \
	  gcloud artifacts docker images list $(PROD_REGION)-docker.pkg.dev/$(PROD_PROJECT_ID)/$(PROD_ARTIFACT_REPO) \
	    --filter="package=$$svc AND tags:$(PROD_IMAGE_TAG)" --format="table(package,tags)" || true; \
	done
