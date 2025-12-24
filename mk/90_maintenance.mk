## ============================================================
## メンテナンス運用（ops/maintenance/ に移譲）
## ============================================================
## 注意:
##   - メンテナンス専用の Makefile は ops/maintenance/Makefile にあります
##   - このセクションはラッパーコマンドとして提供
##
## 直接実行する場合:
##   cd ops/maintenance && make deploy PROJECT_ID=xxx
##
## ルートから実行する場合（ラッパー）:
##   make maintenance-deploy PROJECT_ID=xxx
##   make maintenance-test PROJECT_ID=xxx
##   make maintenance-setup-build PROJECT_ID=xxx
##   make maintenance-enable-apis PROJECT_ID=xxx
## ============================================================

##@ Maintenance

.PHONY: maintenance-deploy maintenance-test maintenance-check maintenance-setup-iap \
        maintenance-setup-build maintenance-setup-cloudbuild maintenance-enable-apis \
        maintenance-test-direct maintenance-build-log maintenance-deploy-local \
        maintenance-on maintenance-off maintenance-status \
        maintenance-clean maintenance-help

maintenance-help: ## Show maintenance operations help
	@echo "[info] メンテナンス運用コマンド"
	@echo "       詳細: ops/maintenance/Makefile"
	@echo ""
	@$(MAKE) -C ops/maintenance help

maintenance-enable-apis: ## Enable required GCP APIs (PROJECT_ID=xxx)
	@$(MAKE) -C ops/maintenance enable-apis PROJECT_ID=$(PROJECT_ID)

maintenance-setup-build: ## Setup Cloud Build permissions (PROJECT_ID=xxx)
	@$(MAKE) -C ops/maintenance setup-build-permissions PROJECT_ID=$(PROJECT_ID)

# 後方互換性のための alias（非推奨）
maintenance-setup-cloudbuild: maintenance-setup-build ## [Deprecated] Use maintenance-setup-build instead
	@echo "[warn] ⚠️  'maintenance-setup-cloudbuild' is deprecated."
	@echo "[warn] Please use 'maintenance-setup-build' instead."

maintenance-deploy: ## Deploy maintenance page to Cloud Run (PROJECT_ID=xxx)
	@$(MAKE) -C ops/maintenance deploy PROJECT_ID=$(PROJECT_ID)

maintenance-deploy-local: ## Deploy maintenance page locally (PROJECT_ID=xxx)
	@$(MAKE) -C ops/maintenance deploy-local PROJECT_ID=$(PROJECT_ID)

maintenance-test: ## Test maintenance page deployment (PROJECT_ID=xxx)
	@$(MAKE) -C ops/maintenance test PROJECT_ID=$(PROJECT_ID)

maintenance-test-direct: ## Test maintenance page directly (PROJECT_ID=xxx)
	@$(MAKE) -C ops/maintenance test-direct PROJECT_ID=$(PROJECT_ID)

maintenance-build-log: ## Check Cloud Build log (PROJECT_ID=xxx BUILD_ID=xxx)
	@$(MAKE) -C ops/maintenance check-build-log PROJECT_ID=$(PROJECT_ID) BUILD_ID=$(BUILD_ID)

maintenance-on: ## Enable maintenance mode (PROJECT_ID=xxx)
	@$(MAKE) -C ops/maintenance maintenance-on PROJECT_ID=$(PROJECT_ID)

maintenance-off: ## Disable maintenance mode (PROJECT_ID=xxx)
	@$(MAKE) -C ops/maintenance maintenance-off PROJECT_ID=$(PROJECT_ID)

maintenance-status: ## Check maintenance mode status (PROJECT_ID=xxx)
	@$(MAKE) -C ops/maintenance maintenance-status PROJECT_ID=$(PROJECT_ID)

maintenance-check: ## Check maintenance page deployment (PROJECT_ID=xxx)
	@$(MAKE) -C ops/maintenance check PROJECT_ID=$(PROJECT_ID)

maintenance-setup-iap: ## Setup Identity-Aware Proxy (PROJECT_ID=xxx)
	@$(MAKE) -C ops/maintenance setup-iap PROJECT_ID=$(PROJECT_ID)

maintenance-clean: ## Clean up maintenance page resources (PROJECT_ID=xxx)
	@$(MAKE) -C ops/maintenance clean PROJECT_ID=$(PROJECT_ID)
