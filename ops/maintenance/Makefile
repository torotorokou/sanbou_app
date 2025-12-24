## =============================================================
## Makefile : メンテナンス運用ツール（ops/maintenance/）
## =============================================================
##
## 目的:
##   - Cloud Run メンテナンスページの管理
##   - アプリケーション本体とは独立した運用ツール
##
## 使い方:
##   cd ops/maintenance
##   make deploy PROJECT_ID=honest-sanbou-app-prod
##   make test PROJECT_ID=honest-sanbou-app-prod
##   make setup-iap PROJECT_ID=honest-sanbou-app-prod
##
## または、ルートディレクトリから:
##   make -C ops/maintenance deploy PROJECT_ID=honest-sanbou-app-prod
##
## =============================================================

## デフォルト設定
SERVICE_NAME ?= maintenance-page
REGION ?= asia-northeast1
PROJECT_ID ?=

# Cloud Run の設定
MIN_INSTANCES ?= 0
MAX_INSTANCES ?= 10
CPU ?= 1
MEMORY ?= 256Mi
TIMEOUT ?= 10s
CONCURRENCY ?= 80

# ディレクトリ
CLOUDRUN_DIR := cloudrun

.PHONY: help deploy test check setup-iap setup-cloudbuild-permissions clean

## ============================================================
## ヘルプ
## ============================================================
help:
	@echo "=== メンテナンス運用 Makefile ==="
	@echo ""
	@echo "前提条件:"
	@echo "  PROJECT_ID=xxx を指定して実行してください"
	@echo ""
	@echo "初回セットアップ:"
	@echo "  make setup-cloudbuild-permissions PROJECT_ID=xxx"
	@echo "  make deploy PROJECT_ID=xxx"
	@echo "  make setup-iap PROJECT_ID=xxx"
	@echo ""
	@echo "よく使うコマンド:"
	@echo "  make deploy PROJECT_ID=xxx     - Cloud Run にデプロイ"
	@echo "  make test PROJECT_ID=xxx       - 動作確認（認証付きリクエスト）"
	@echo "  make check PROJECT_ID=xxx      - サービス状態確認"
	@echo ""
	@echo "トラブルシューティング:"
	@echo "  make setup-cloudbuild-permissions PROJECT_ID=xxx"
	@echo ""
	@echo "設定:"
	@echo "  SERVICE_NAME = $(SERVICE_NAME)"
	@echo "  REGION       = $(REGION)"
	@echo "  MIN_INSTANCES= $(MIN_INSTANCES)"
	@echo "  MAX_INSTANCES= $(MAX_INSTANCES)"
	@echo "  CPU          = $(CPU)"
	@echo "  MEMORY       = $(MEMORY)"
	@echo ""

## ============================================================
## Cloud Build 権限設定（初回デプロイ前に必須）
## ============================================================
setup-cloudbuild-permissions:
	@if [ -z "$(PROJECT_ID)" ]; then \
	  echo "[error] PROJECT_ID is required."; \
	  echo "Usage: make setup-cloudbuild-permissions PROJECT_ID=your-project-id"; \
	  exit 1; \
	fi
	@echo "[info] Setting up Cloud Build permissions for project $(PROJECT_ID)"
	@PROJECT_NUMBER=$$(gcloud projects describe $(PROJECT_ID) --format="value(projectNumber)"); \
	echo "[info] Project Number: $$PROJECT_NUMBER"; \
	echo ""; \
	echo "[info] Granting required roles to service accounts..."; \
	echo "  1. Storage Admin to Compute Engine default SA"; \
	gcloud projects add-iam-policy-binding $(PROJECT_ID) \
	  --member="serviceAccount:$$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
	  --role="roles/storage.admin" \
	  --condition=None && \
	echo "  2. Cloud Run Admin to Cloud Build SA"; \
	gcloud projects add-iam-policy-binding $(PROJECT_ID) \
	  --member="serviceAccount:$$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
	  --role="roles/run.admin" \
	  --condition=None && \
	echo "  3. Service Account User to Cloud Build SA"; \
	gcloud projects add-iam-policy-binding $(PROJECT_ID) \
	  --member="serviceAccount:$$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
	  --role="roles/iam.serviceAccountUser" \
	  --condition=None
	@echo ""
	@echo "[ok] ✅ Cloud Build permissions configured successfully"
	@echo "[info] ⏱️  Permissions may take a few minutes to propagate"
	@echo ""
	@echo "Next step: make deploy PROJECT_ID=$(PROJECT_ID)"

## ============================================================
## Cloud Run デプロイ
## ============================================================
deploy:
	@if [ -z "$(PROJECT_ID)" ]; then \
	  echo "[error] PROJECT_ID is required."; \
	  echo "Usage: make deploy PROJECT_ID=your-project-id"; \
	  exit 1; \
	fi
	@echo "[info] Deploying maintenance page to Cloud Run"
	@echo "       Project: $(PROJECT_ID)"
	@echo "       Region: $(REGION)"
	@echo "       Service: $(SERVICE_NAME)"
	@echo ""
	@echo "[info] ⚠️  First-time deployment?"
	@echo "       If you get permission errors, run:"
	@echo "       make setup-cloudbuild-permissions PROJECT_ID=$(PROJECT_ID)"
	@echo ""
	cd $(CLOUDRUN_DIR) && \
	gcloud run deploy $(SERVICE_NAME) \
	  --source . \
	  --platform managed \
	  --region $(REGION) \
	  --project $(PROJECT_ID) \
	  --no-allow-unauthenticated \
	  --min-instances $(MIN_INSTANCES) \
	  --max-instances $(MAX_INSTANCES) \
	  --cpu $(CPU) \
	  --memory $(MEMORY) \
	  --timeout $(TIMEOUT) \
	  --concurrency $(CONCURRENCY) \
	  --ingress internal-and-cloud-load-balancing
	@echo ""
	@echo "[ok] ✅ Deployment completed"
	@echo ""
	@echo "[info] 📋 Next steps:"
	@echo "  1. Configure IAP Service Agent:"
	@echo "     make setup-iap PROJECT_ID=$(PROJECT_ID)"
	@echo ""
	@echo "  2. Verify deployment:"
	@echo "     make test PROJECT_ID=$(PROJECT_ID)"
	@echo ""
	@echo "  3. See cloudrun/README.md for LB configuration"

## ============================================================
## 動作確認（認証付きリクエスト）
## ============================================================
test:
	@if [ -z "$(PROJECT_ID)" ]; then \
	  echo "[error] PROJECT_ID is required."; \
	  echo "Usage: make test PROJECT_ID=your-project-id"; \
	  exit 1; \
	fi
	@echo "[info] Testing maintenance page (authenticated request)"
	@SERVICE_URL=$$(gcloud run services describe $(SERVICE_NAME) \
	  --region $(REGION) \
	  --project $(PROJECT_ID) \
	  --format="value(status.url)" 2>/dev/null); \
	if [ -z "$$SERVICE_URL" ]; then \
	  echo "[error] ❌ Service not found."; \
	  echo "Deploy first: make deploy PROJECT_ID=$(PROJECT_ID)"; \
	  exit 1; \
	fi; \
	TOKEN=$$(gcloud auth print-identity-token 2>/dev/null); \
	if [ -z "$$TOKEN" ]; then \
	  echo "[error] ❌ Failed to get identity token."; \
	  echo "Run: gcloud auth login"; \
	  exit 1; \
	fi; \
	echo "[info] Service URL: $$SERVICE_URL"; \
	echo "[info] Sending authenticated request..."; \
	echo ""; \
	curl -i -H "Authorization: Bearer $$TOKEN" "$$SERVICE_URL" || true
	@echo ""
	@echo "[info] ✅ If you see HTTP 503 with maintenance page HTML, it's working!"

## ============================================================
## サービス状態確認
## ============================================================
check:
	@if [ -z "$(PROJECT_ID)" ]; then \
	  echo "[error] PROJECT_ID is required."; \
	  echo "Usage: make check PROJECT_ID=your-project-id"; \
	  exit 1; \
	fi
	@echo "[info] Checking Cloud Run service status"
	@gcloud run services describe $(SERVICE_NAME) \
	  --region $(REGION) \
	  --project $(PROJECT_ID) \
	  --format="table(status.url,status.conditions[0].status,status.conditions[0].type)" 2>/dev/null || \
	  echo "[warn] ⚠️  Service not deployed yet"

## ============================================================
## IAP Service Agent 設定
## ============================================================
setup-iap:
	@if [ -z "$(PROJECT_ID)" ]; then \
	  echo "[error] PROJECT_ID is required."; \
	  echo "Usage: make setup-iap PROJECT_ID=your-project-id"; \
	  exit 1; \
	fi
	@echo "[info] Setting up IAP Service Agent for Cloud Run invoker"
	@echo ""
	@echo "[info] Step 1/3: Create IAP service identity"
	@gcloud beta services identity create \
	  --service=iap.googleapis.com \
	  --project=$(PROJECT_ID) 2>/dev/null || echo "[info] Identity may already exist"
	@echo ""
	@echo "[info] Step 2/3: Get project number"
	@PROJECT_NUMBER=$$(gcloud projects describe $(PROJECT_ID) --format="value(projectNumber)"); \
	echo "[info] Project Number: $$PROJECT_NUMBER"; \
	echo ""; \
	echo "[info] Step 3/3: Grant roles/run.invoker to IAP Service Agent"; \
	gcloud run services add-iam-policy-binding $(SERVICE_NAME) \
	  --region=$(REGION) \
	  --project=$(PROJECT_ID) \
	  --member="serviceAccount:service-$$PROJECT_NUMBER@gcp-sa-iap.iam.gserviceaccount.com" \
	  --role="roles/run.invoker"
	@echo ""
	@echo "[ok] ✅ IAP setup completed"
	@echo ""
	@echo "[info] Now you can access the service via IAP + Load Balancer"

## ============================================================
## クリーンアップ（サービス削除）
## ============================================================
clean:
	@if [ -z "$(PROJECT_ID)" ]; then \
	  echo "[error] PROJECT_ID is required."; \
	  echo "Usage: make clean PROJECT_ID=your-project-id"; \
	  exit 1; \
	fi
	@echo "[warn] ⚠️  This will DELETE the Cloud Run service: $(SERVICE_NAME)"
	@echo "[warn] Project: $(PROJECT_ID)"
	@echo "[warn] Region: $(REGION)"
	@echo ""
	@read -p "Are you sure? (yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
	  echo "[info] Deleting service..."; \
	  gcloud run services delete $(SERVICE_NAME) \
	    --region $(REGION) \
	    --project $(PROJECT_ID) \
	    --quiet; \
	  echo "[ok] ✅ Service deleted"; \
	else \
	  echo "[info] Cancelled"; \
	fi
