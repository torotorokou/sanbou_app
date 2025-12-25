## ============================================================
## Git Hooks Management
## ============================================================
## このモジュールは Git hooks の導入・実行・更新を管理します。
##
## Pre-commit hooks の正本は .pre-commit-config.yaml です。
## Git hook の実体は tools/git-hooks/ にあり、
## core.hooksPath で参照されます。
##
## コマンド:
##   make hooks-install  - Git hooks を初回セットアップ
##   make hooks-run      - 全ファイルでチェック実行
##   make hooks-update   - hooks の自動アップデート
##   make hooks-clean    - hooks の設定をクリーン
## ============================================================

.PHONY: hooks-install hooks-run hooks-update hooks-clean

# pre-commit バイナリの検出
# 1) PATH 上の pre-commit
# 2) プロジェクト配下の .venv/bin/pre-commit
PRE_COMMIT_BIN := $(shell if command -v pre-commit >/dev/null 2>&1; then command -v pre-commit; elif [ -x .venv/bin/pre-commit ]; then echo $(PWD)/.venv/bin/pre-commit; fi)

## hooks-install: Git hooks を初回セットアップ（pre-commit install + hooksPath設定）
hooks-install: ## @Category(Hooks) Git hooks を初回セットアップ
	@echo "========================================="
	@echo "🔧 Git Hooks セットアップ開始"
	@echo "========================================="
	@echo ""
	@echo "📦 1. pre-commit のインストール確認..."
	@PRE_COMMIT_BIN="$(PRE_COMMIT_BIN)"; \
	if [ -z "$$PRE_COMMIT_BIN" ]; then \
		echo "❌ エラー: pre-commit が見つかりませんでした"; \
		echo ""; \
		echo "以下のコマンドでインストールしてください:"; \
		echo "  pip install pre-commit"; \
		echo ""; \
		exit 1; \
	fi; \
	echo "✅ pre-commit を検出: $$PRE_COMMIT_BIN"
	@echo ""
	@echo "🔗 2. Git hooks の設定..."
	git config core.hooksPath tools/git-hooks
	@echo "✅ core.hooksPath を tools/git-hooks に設定しました"
	@echo ""
	@echo "📝 3. Pre-commit 環境を事前セットアップ (install-hooks)..."
	@if "$(PRE_COMMIT_BIN)" install-hooks; then \
		echo "✅ Pre-commit 環境をセットアップしました"; \
	else \
		echo "⚠️  install-hooks が警告を返しました。初回の pre-commit 実行時に再試行されます。"; \
		echo "   依存パッケージ (例: libatomic1) が不足している場合はインストールしてください。"; \
	fi
	@echo ""
	@echo "✅ Git hooks のセットアップが完了しました！"
	@echo ""
	@echo "📚 使い方:"
	@echo "  - make hooks-run     # 全ファイルでチェック実行"
	@echo "  - make hooks-update  # hooks の自動アップデート"
	@echo "  - git commit         # 自動的に pre-commit が実行されます"
	@echo "  - git push           # 自動的に pre-push が実行されます"
	@echo ""

## hooks-run: 全ファイルで pre-commit チェックを実行
hooks-run: ## @Category(Hooks) 全ファイルで pre-commit チェックを実行
	@echo "🔍 Pre-commit チェックを全ファイルで実行中..."
	@echo ""
	"$(PRE_COMMIT_BIN)" run --all-files

## hooks-update: Pre-commit hooks を自動アップデート
hooks-update: ## @Category(Hooks) Pre-commit hooks を自動アップデート
	@echo "📦 Pre-commit hooks を自動アップデート中..."
	@echo ""
	"$(PRE_COMMIT_BIN)" autoupdate
	@echo ""
	@echo "✅ アップデート完了"
	@echo ""
	@echo "💡 .pre-commit-config.yaml を確認し、変更があればコミットしてください"

## hooks-clean: Git hooks の設定をクリーン（hooksPath を解除）
hooks-clean: ## @Category(Hooks) Git hooks の設定をクリーン
	@echo "🧹 Git hooks の設定をクリーン中..."
	@echo ""
	git config --unset core.hooksPath || true
	"$(PRE_COMMIT_BIN)" uninstall || true
	@echo ""
	@echo "✅ クリーン完了"
	@echo ""
	@echo "💡 再度セットアップする場合は 'make hooks-install' を実行してください"
