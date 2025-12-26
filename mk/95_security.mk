## ============================================================
## セキュリティスキャン（Trivy）
## ============================================================

##@ Security

.PHONY: scan-images scan-local-images install-trivy security-check \
        scan-stg-images scan-prod-images

# Trivy インストール確認・インストール
install-trivy: ## Install Trivy scanner (if not present)
	@echo "=== Checking Trivy installation ==="
	@if ! command -v trivy &> /dev/null; then \
	  echo "Trivy not found. Installing..."; \
	  if [ "$$(uname)" = "Darwin" ]; then \
	    brew install aquasecurity/trivy/trivy; \
	  elif [ "$$(uname)" = "Linux" ]; then \
	    wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -; \
	    echo "deb https://aquasecurity.github.io/trivy-repo/deb $$(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list; \
	    sudo apt-get update && sudo apt-get install trivy; \
	  else \
	    echo "Unsupported OS. Please install Trivy manually: https://aquasecurity.github.io/trivy/"; \
	    exit 1; \
	  fi; \
	else \
	  echo "✅ Trivy is already installed ($$(trivy --version))"; \
	fi

# ローカルビルド済みイメージをスキャン
scan-local-images: install-trivy ## Scan local Docker images for vulnerabilities
	@echo "=== Scanning local Docker images for vulnerabilities ==="
	@SERVICES="frontend core_api ai_api ledger_api rag_api manual_api plan_worker"; \
	for svc in $$SERVICES; do \
	  IMAGE_NAME="local_dev-$$svc"; \
	  if docker images | grep -q "$$IMAGE_NAME"; then \
	    echo ""; \
	    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	    echo "Scanning: $$IMAGE_NAME"; \
	    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	    trivy image --severity HIGH,CRITICAL --exit-code 0 $$IMAGE_NAME || true; \
	  else \
	    echo "⚠️  Image not found: $$IMAGE_NAME (skipping)"; \
	  fi; \
	done
	@echo ""
	@echo "✅ Scan completed. Review HIGH/CRITICAL vulnerabilities above."

# Artifact Registry のイメージをスキャン（STG）
scan-stg-images: install-trivy ## Scan STG images in Artifact Registry (STG_IMAGE_TAG=xxx)
	@echo "=== Scanning STG images in Artifact Registry ==="
	@SERVICES="core_api plan_worker ai_api ledger_api rag_api manual_api nginx"; \
	for svc in $$SERVICES; do \
	  IMAGE="$(STG_IMAGE_REGISTRY)/$$svc:$(STG_IMAGE_TAG)"; \
	  echo ""; \
	  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	  echo "Scanning: $$IMAGE"; \
	  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	  trivy image --severity HIGH,CRITICAL --exit-code 1 $$IMAGE || \
	    (echo "❌ Vulnerabilities found in $$IMAGE"; exit 1); \
	done
	@echo "✅ All STG images passed security scan"

# Artifact Registry のイメージをスキャン（PROD）
scan-prod-images: install-trivy ## Scan PROD images in Artifact Registry (PROD_IMAGE_TAG=xxx)
	@echo "=== Scanning PROD images in Artifact Registry ==="
	@SERVICES="core_api plan_worker ai_api ledger_api rag_api manual_api nginx"; \
	for svc in $$SERVICES; do \
	  IMAGE="$(PROD_IMAGE_REGISTRY)/$$svc:$(PROD_IMAGE_TAG)"; \
	  echo ""; \
	  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	  echo "Scanning: $$IMAGE"; \
	  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	  trivy image --severity HIGH,CRITICAL --exit-code 1 $$IMAGE || \
	    (echo "❌ Vulnerabilities found in $$IMAGE"; exit 1); \
	done
	@echo "✅ All PROD images passed security scan"

# エイリアス（デフォルトはローカルスキャン）
scan-images: scan-local-images ## Alias for scan-local-images

# CI/CD パイプライン用の総合セキュリティチェック
security-check: scan-local-images ## Comprehensive security check for CI/CD
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "✅ Security checks completed successfully"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
