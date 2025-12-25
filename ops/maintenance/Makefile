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
##   make deploy
##   make test
##   make setup-iap
##
## または、ルートディレクトリから:
##   make maintenance-deploy PROJECT_ID=honest-sanbou-app-prod
##   make maintenance-test PROJECT_ID=honest-sanbou-app-prod
##
## 設定:
##   .env ファイルで PROJECT_ID などを設定してください。
##   テンプレート: .env.example
##
## =============================================================

# .env ファイルがあれば読み込む（Git 管理外）
-include .env

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

# Artifact Registry リポジトリ（デプロイ用）
ARTIFACT_REPO ?= sanbou-app

# LB 設定（メンテナンスモード切替用）
URL_MAP_NAME ?= sanbou-prod-lb
PROD_BACKEND_SERVICE ?= sanbou-prod-backend
MAINTENANCE_BACKEND_SERVICE ?= maintenance-page-backend

.PHONY: help deploy deploy-local test check setup-iap setup-build-permissions clean \
        enable-apis setup-build-permissions check-build-log test-direct \
        maintenance-on maintenance-off maintenance-status

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
## API有効化（初回のみ）
## ============================================================
enable-apis:
	@if [ -z "$(PROJECT_ID)" ]; then \
	  echo "[error] PROJECT_ID is required."; \
	  echo "Usage: make enable-apis PROJECT_ID=your-project-id"; \
	  exit 1; \
	fi
	@echo "[info] Enabling required APIs for project $(PROJECT_ID)"
	@echo "  - cloudbuild.googleapis.com"
	@echo "  - run.googleapis.com"
	@echo "  - artifactregistry.googleapis.com"
	gcloud services enable \
	  cloudbuild.googleapis.com \
	  run.googleapis.com \
	  artifactregistry.googleapis.com \
	  --project=$(PROJECT_ID)
	@echo "[ok] ✅ APIs enabled"

## ============================================================
## Cloud Build 権限設定（最小権限版）
## 説明:
##   Cloud Build SA に必要最小限のロールを付与します。
##   - artifactregistry.writer: イメージのpush権限
##   - run.admin: Cloud Run サービスの作成/更新
##   - iam.serviceAccountUser: サービスアカウントの使用
## ============================================================
setup-build-permissions:
	@if [ -z "$(PROJECT_ID)" ]; then \
	  echo "[error] PROJECT_ID is required."; \
	  echo "Usage: make setup-build-permissions PROJECT_ID=your-project-id"; \
	  exit 1; \
	fi
	@echo "[info] Setting up Cloud Build permissions (minimal required)"
	@PROJECT_NUMBER=$$(gcloud projects describe $(PROJECT_ID) --format="value(projectNumber)"); \
	echo "[info] Project Number: $$PROJECT_NUMBER"; \
	echo "[info] Cloud Build SA: $$PROJECT_NUMBER@cloudbuild.gserviceaccount.com"; \
	echo ""; \
	echo "[info] Granting minimal required roles..."; \
	echo "  1. artifactregistry.writer (for image push)"; \
	gcloud projects add-iam-policy-binding $(PROJECT_ID) \
	  --member="serviceAccount:$$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
	  --role="roles/artifactregistry.writer" \
	  --condition=None && \
	echo "  2. run.admin (for Cloud Run deployment)"; \
	gcloud projects add-iam-policy-binding $(PROJECT_ID) \
	  --member="serviceAccount:$$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
	  --role="roles/run.admin" \
	  --condition=None && \
	echo "  3. iam.serviceAccountUser (for SA usage)"; \
	gcloud projects add-iam-policy-binding $(PROJECT_ID) \
	  --member="serviceAccount:$$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
	  --role="roles/iam.serviceAccountUser" \
	  --condition=None
	@echo ""
	@echo "[ok] ✅ Minimal permissions configured successfully"
	@echo "[info] ⏱️  Permissions may take a few minutes to propagate"
	@echo ""
	@echo "Next step: make deploy PROJECT_ID=$(PROJECT_ID)"

## ============================================================
## Cloud Build ログ確認（デプロイ失敗時）
## 使い方:
##   make check-build-log PROJECT_ID=xxx BUILD_ID=<失敗したビルドID>
## ============================================================
check-build-log:
	@if [ -z "$(PROJECT_ID)" ]; then \
	  echo "[error] PROJECT_ID is required."; \
	  exit 1; \
	fi
	@if [ -z "$(BUILD_ID)" ]; then \
	  echo "[info] BUILD_ID not specified, showing recent builds..."; \
	  echo ""; \
	  gcloud builds list \
	    --region=$(REGION) \
	    --project=$(PROJECT_ID) \
	    --limit=5 \
	    --format="table(id,status,logUrl)"; \
	  echo ""; \
	  echo "[info] To check specific build log:"; \
	  echo "       make check-build-log PROJECT_ID=$(PROJECT_ID) BUILD_ID=<build-id>"; \
	else \
	  echo "[info] Fetching build log for BUILD_ID=$(BUILD_ID)"; \
	  gcloud builds log $(BUILD_ID) \
	    --region=$(REGION) \
	    --project=$(PROJECT_ID) 2>&1 | tail -100; \
	fi

## 後方互換性のための alias
setup-cloudbuild-permissions: setup-build-permissions
	@echo "[warn] ⚠️  'setup-cloudbuild-permissions' is deprecated."
	@echo "[warn] Please use 'setup-build-permissions' instead."

## ============================================================
## Cloud Run デプロイ（Cloud Build 使用）
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
	@echo "[info] ⚠️  First-time deployment? Run these first:"
	@echo "       1. make enable-apis PROJECT_ID=$(PROJECT_ID)"
	@echo "       2. make setup-build-permissions PROJECT_ID=$(PROJECT_ID)"
	@echo ""
	@echo "[info] 🔍 If build fails, check logs:"
	@echo "       make check-build-log PROJECT_ID=$(PROJECT_ID)"
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
## Cloud Run デプロイ（ローカルビルド → Artifact Registry → Cloud Run）
## 説明:
##   Cloud Build が失敗する場合の回避策。
##   Docker でローカルビルドし、Artifact Registry に push してデプロイします。
## 前提条件:
##   - Docker がインストール済み
##   - gcloud auth configure-docker 実行済み
## ============================================================
deploy-local:
	@if [ -z "$(PROJECT_ID)" ]; then \
	  echo "[error] PROJECT_ID is required."; \
	  echo "Usage: make deploy-local PROJECT_ID=your-project-id"; \
	  exit 1; \
	fi
	@echo "[info] 🏗️  Local build deployment (Docker → Artifact Registry → Cloud Run)"
	@echo "       Project: $(PROJECT_ID)"
	@echo "       Region: $(REGION)"
	@echo "       Service: $(SERVICE_NAME)"
	@echo ""
	@IMAGE_URL="$(REGION)-docker.pkg.dev/$(PROJECT_ID)/$(ARTIFACT_REPO)/$(SERVICE_NAME):latest"; \
	echo "[info] Step 1/3: Building Docker image locally..."; \
	cd $(CLOUDRUN_DIR) && docker build -t $$IMAGE_URL . || { \
	  echo "[error] ❌ Docker build failed"; \
	  exit 1; \
	}; \
	echo "[ok] ✅ Docker image built"; \
	echo ""; \
	echo "[info] Step 2/3: Pushing to Artifact Registry..."; \
	echo "       Image: $$IMAGE_URL"; \
	docker push $$IMAGE_URL || { \
	  echo "[error] ❌ Docker push failed"; \
	  echo "[info] Run: gcloud auth configure-docker $(REGION)-docker.pkg.dev"; \
	  exit 1; \
	}; \
	echo "[ok] ✅ Image pushed"; \
	echo ""; \
	echo "[info] Step 3/3: Deploying to Cloud Run..."; \
	gcloud run deploy $(SERVICE_NAME) \
	  --image $$IMAGE_URL \
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
	@echo "[ok] ✅ Deployment completed (local build)"
	@echo ""
	@echo "[info] 📋 Next steps:"
	@echo "  1. Verify deployment: make check PROJECT_ID=$(PROJECT_ID)"
	@echo "  2. Test: make test-direct PROJECT_ID=$(PROJECT_ID)"


## ============================================================
## 動作確認（認証付きリクエスト）
## 注意:
##   ingress=internal-and-cloud-load-balancing の場合、
##   *.a.run.app への直接アクセスは 404 になることがあります。
##   本番では LB 経由（https://sanbou-app.jp/）で確認してください。
##   直接テストする場合は 'make test-direct' を使用してください。
## ============================================================
test:
	@if [ -z "$(PROJECT_ID)" ]; then \
	  echo "[error] PROJECT_ID is required."; \
	  echo "Usage: make test PROJECT_ID=your-project-id"; \
	  exit 1; \
	fi
	@echo "[info] ⚠️  NOTE: This test may return 404 due to ingress restrictions."
	@echo "       For production testing, use LB URL (https://sanbou-app.jp/)"
	@echo "       For direct URL test, use: make test-direct PROJECT_ID=$(PROJECT_ID)"
	@echo ""
	@SERVICE_URL=$$(gcloud run services describe $(SERVICE_NAME) \
	  --region $(REGION) \
	  --project $(PROJECT_ID) \
	  --format="value(status.url)" 2>/dev/null); \
	if [ -z "$$SERVICE_URL" ]; then \
	  echo "[error] ❌ Service not found."; \
	  echo "Deploy first: make deploy PROJECT_ID=$(PROJECT_ID)"; \
	  exit 1; \
	fi; \
	echo "[info] Service URL: $$SERVICE_URL"; \
	TOKEN=$$(gcloud auth print-identity-token --audiences="$$SERVICE_URL" 2>/dev/null); \
	if [ -z "$$TOKEN" ]; then \
	  echo "[error] ❌ Failed to get identity token."; \
	  echo "Run: gcloud auth login"; \
	  exit 1; \
	fi; \
	echo "[info] Sending authenticated request..."; \
	echo ""; \
	RESPONSE=$$(curl -s -o /tmp/maintenance-test.html -w "%%{http_code}" -H "Authorization: Bearer $$TOKEN" "$$SERVICE_URL"); \
	if [ "$$RESPONSE" = "503" ]; then \
	  echo "[ok] ✅ HTTP 503 received - maintenance page is working!"; \
	  head -20 /tmp/maintenance-test.html | grep -q "メンテナンス中" && echo "[ok] ✅ HTML content verified"; \
	elif [ "$$RESPONSE" = "404" ]; then \
	  echo "[warn] ⚠️  HTTP 404 - This is expected with ingress=internal-and-cloud-load-balancing"; \
	  echo "[info] The service is deployed but not accessible via direct URL."; \
	  echo "[info] Test via LB or use: make test-direct PROJECT_ID=$(PROJECT_ID)"; \
	else \
	  echo "[error] ❌ Unexpected response: HTTP $$RESPONSE"; \
	  curl -i -H "Authorization: Bearer $$TOKEN" "$$SERVICE_URL"; \
	fi; \
	rm -f /tmp/maintenance-test.html

## ============================================================
## 直接URL動作確認（一時的に ingress=all に変更してテスト）
## 注意: 短時間だけ公開状態になります。テスト後すぐに戻します。
## ============================================================
test-direct:
	@if [ -z "$(PROJECT_ID)" ]; then \
	  echo "[error] PROJECT_ID is required."; \
	  exit 1; \
	fi
	@echo "[warn] ⚠️  This will temporarily change ingress to 'all'"
	@echo "[warn] Testing and reverting in 30 seconds..."
	@echo ""
	@SERVICE_URL=$$(gcloud run services describe $(SERVICE_NAME) \
	  --region $(REGION) \
	  --project $(PROJECT_ID) \
	  --format="value(status.url)" 2>/dev/null); \
	if [ -z "$$SERVICE_URL" ]; then \
	  echo "[error] ❌ Service not found."; \
	  exit 1; \
	fi; \
	echo "[info] Step 1/4: Setting ingress=all temporarily..."; \
	gcloud run services update $(SERVICE_NAME) \
	  --region=$(REGION) \
	  --project=$(PROJECT_ID) \
	  --ingress=all \
	  --quiet; \
	sleep 5; \
	echo ""; \
	echo "[info] Step 2/4: Allowing unauthenticated access temporarily..."; \
	gcloud run services add-iam-policy-binding $(SERVICE_NAME) \
	  --region=$(REGION) \
	  --project=$(PROJECT_ID) \
	  --member="allUsers" \
	  --role="roles/run.invoker" \
	  --quiet; \
	sleep 5; \
	echo ""; \
	echo "[info] Step 3/4: Testing direct URL (no auth)..."; \
	RESPONSE=$$(curl -s -o /tmp/maintenance-test-direct.html -w "%%{http_code}" "$$SERVICE_URL"); \
	if [ "$$RESPONSE" = "503" ]; then \
	  echo "[ok] ✅ HTTP 503 received - maintenance page is working!"; \
	  head -20 /tmp/maintenance-test-direct.html | grep -q "メンテナンス中" && echo "[ok] ✅ HTML content verified"; \
	else \
	  echo "[error] ❌ Unexpected response: HTTP $$RESPONSE"; \
	  curl -i "$$SERVICE_URL"; \
	fi; \
	rm -f /tmp/maintenance-test-direct.html; \
	echo ""; \
	echo "[info] Step 4/4: Reverting security settings..."; \
	gcloud run services remove-iam-policy-binding $(SERVICE_NAME) \
	  --region=$(REGION) \
	  --project=$(PROJECT_ID) \
	  --member="allUsers" \
	  --role="roles/run.invoker" \
	  --quiet; \
	gcloud run services update $(SERVICE_NAME) \
	  --region=$(REGION) \
	  --project=$(PROJECT_ID) \
	  --ingress=internal-and-cloud-load-balancing \
	  --quiet; \
	echo "[ok] ✅ Security settings reverted. Test completed."

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

## ============================================================

## ============================================================
## メンテナンスモード ON（本番 → メンテナンスページ）
## ============================================================
maintenance-on:
	@if [ -z "$(PROJECT_ID)" ]; then \
	  echo "[error] PROJECT_ID is required."; \
	  echo "Usage: make maintenance-on PROJECT_ID=your-project-id"; \
	  exit 1; \
	fi
	@echo "[info] 🔧 Switching to MAINTENANCE MODE"
	@echo "       URL Map: $(URL_MAP_NAME)"
	@echo "       Backend: $(PROD_BACKEND_SERVICE) → $(MAINTENANCE_BACKEND_SERVICE)"
	@echo ""
	@CURRENT=$$(gcloud compute url-maps describe $(URL_MAP_NAME) \
	  --global \
	  --project=$(PROJECT_ID) \
	  --format="value(defaultService)" 2>/dev/null | grep -o '[^/]*$$'); \
	if [ "$$CURRENT" = "$(MAINTENANCE_BACKEND_SERVICE)" ]; then \
	  echo "[warn] ⚠️  Already in maintenance mode"; \
	  exit 0; \
	fi; \
	gcloud compute url-maps set-default-service $(URL_MAP_NAME) \
	  --default-service $(MAINTENANCE_BACKEND_SERVICE) \
	  --global \
	  --project=$(PROJECT_ID)
	@echo ""
	@echo "[ok] ✅ Maintenance mode ON"
	@echo "[info] Access: https://honest.sanbou-app.jp/"
	@echo "[info] Users will see HTTP 503 maintenance page"
	@echo ""
	@echo "[info] To exit maintenance mode:"
	@echo "       make maintenance-off PROJECT_ID=$(PROJECT_ID)"

## ============================================================
## メンテナンスモード OFF（メンテナンスページ → 本番）
## ============================================================
maintenance-off:
	@if [ -z "$(PROJECT_ID)" ]; then \
	  echo "[error] PROJECT_ID is required."; \
	  echo "Usage: make maintenance-off PROJECT_ID=your-project-id"; \
	  exit 1; \
	fi
	@echo "[info] ✅ Switching to PRODUCTION MODE"
	@echo "       URL Map: $(URL_MAP_NAME)"
	@echo "       Backend: $(MAINTENANCE_BACKEND_SERVICE) → $(PROD_BACKEND_SERVICE)"
	@echo ""
	@CURRENT=$$(gcloud compute url-maps describe $(URL_MAP_NAME) \
	  --global \
	  --project=$(PROJECT_ID) \
	  --format="value(defaultService)" 2>/dev/null | grep -o '[^/]*$$'); \
	if [ "$$CURRENT" = "$(PROD_BACKEND_SERVICE)" ]; then \
	  echo "[warn] ⚠️  Already in production mode"; \
	  exit 0; \
	fi; \
	gcloud compute url-maps set-default-service $(URL_MAP_NAME) \
	  --default-service $(PROD_BACKEND_SERVICE) \
	  --global \
	  --project=$(PROJECT_ID)
	@echo ""
	@echo "[ok] ✅ Production mode ON"
	@echo "[info] Access: https://honest.sanbou-app.jp/"
	@echo "[info] Application is now serving normally"

## ============================================================
## メンテナンスモード状態確認
## ============================================================
maintenance-status:
	@if [ -z "$(PROJECT_ID)" ]; then \
	  echo "[error] PROJECT_ID is required."; \
	  echo "Usage: make maintenance-status PROJECT_ID=your-project-id"; \
	  exit 1; \
	fi
	@echo "[info] Checking maintenance mode status..."
	@echo ""
	@CURRENT=$$(gcloud compute url-maps describe $(URL_MAP_NAME) \
	  --global \
	  --project=$(PROJECT_ID) \
	  --format="value(defaultService)" 2>/dev/null | grep -o '[^/]*$$'); \
	echo "[info] URL Map: $(URL_MAP_NAME)"; \
	echo "[info] Current Backend: $$CURRENT"; \
	echo ""; \
	if [ "$$CURRENT" = "$(MAINTENANCE_BACKEND_SERVICE)" ]; then \
	  echo "[status] 🔧 MAINTENANCE MODE (503 page active)"; \
	elif [ "$$CURRENT" = "$(PROD_BACKEND_SERVICE)" ]; then \
	  echo "[status] ✅ PRODUCTION MODE (app running)"; \
	else \
	  echo "[status] ⚠️  UNKNOWN MODE ($$CURRENT)"; \
	fi
