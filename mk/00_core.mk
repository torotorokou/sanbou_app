## =============================================================
## mk/00_core.mk - Core definitions and help system
## =============================================================

##@ Help

.PHONY: help
help: ## Show this help message with categorized targets
	@echo ''
	@echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
	@echo '  Makefile : sanbou_app 全環境統合管理ツール'
	@echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
	@echo ''
	@echo '🚀 よく使うコマンド:'
	@echo '  make up ENV=local_dev          環境起動'
	@echo '  make down ENV=local_dev        環境停止'
	@echo '  make logs ENV=local_dev S=xxx  ログ確認'
	@echo '  make al-up-env ENV=local_dev   DBマイグレーション'
	@echo '  make backup ENV=local_dev      バックアップ'
	@echo ''
	@echo '🌍 環境 (ENV):'
	@echo '  local_dev   ローカル開発（自動ビルド）'
	@echo '  local_demo  ローカルデモ'
	@echo '  vm_stg      GCP VM ステージング（Artifact Registry）'
	@echo '  vm_prod     GCP VM 本番（Artifact Registry）'
	@echo ''
	@awk 'BEGIN {FS = ":.*##"; current_category = ""} \
		/^##@/ { current_category = substr($$0, 5); next } \
		/^[a-zA-Z_0-9-]+:.*##/ { \
			if (current_category != "") { \
				if (!(current_category in categories)) { \
					category_order[++cat_count] = current_category; \
					categories[current_category] = 1; \
				} \
				targets[current_category, ++target_count[current_category]] = sprintf("  %-30s %s", $$1, $$2); \
			} \
		} \
		END { \
			for (i = 1; i <= cat_count; i++) { \
				cat = category_order[i]; \
				printf "\n📦 %s:\n", cat; \
				for (j = 1; j <= target_count[cat]; j++) { \
					print targets[cat, j]; \
				} \
			} \
			print ""; \
			print "詳細: MAKEFILE_QUICKREF.md または docs/infrastructure/MAKEFILE_GUIDE.md"; \
			print ""; \
		}' $(MAKEFILE_LIST)
