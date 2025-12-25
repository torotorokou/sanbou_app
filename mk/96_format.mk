# ============================================================
# Formatting & Linting (mk/96_format.mk)
# ============================================================
#
# 初回一括整形とCI用のターゲットを提供
# - 通常のコミット時は pre-commit（staged のみ）を使用
# - 初回や全体整形時のみこのターゲットを使用
#
# ⚠️  WSL2 フリーズ防止:
#   - `pre-commit run --all-files` は禁止（CPU張り付き）
#   - 全体整形は `make fmt-step-all` を使用（直列・対象限定）
#   - 安全なチェックは `scripts/safe_check.sh` を経由
#
# 使い方:
#   make fmt-step-all        # 【推奨】ステップ実行（CPU負荷軽減）
#   make check-light         # 差分のみチェック（軽量）
#   make check-ci            # CI専用（ローカルで実行しない）
#
#   make bootstrap-format    # 【非推奨】初回一括整形
#   make check-format        # 【非推奨】チェックのみ
#
# WSL対策（推奨）:
#   make fmt-step-all        # scripts/format_step_by_step.sh を使用
#   make fmt-step-py-fix     # Python ruff のみ
#   make fmt-step-py         # Python black のみ
#   make fmt-step-fe         # Frontend prettier のみ
#   make fmt-step-fe-fix     # Frontend eslint のみ
#
# ============================================================

.PHONY: bootstrap-format fmt-python fmt-frontend check-format check-python check-frontend
.PHONY: fmt-step-all fmt-step-py-fix fmt-step-py fmt-step-fe fmt-step-fe-fix fmt-step-check
	@echo "   - Python: app/backend/ (migrations除外)"
	@echo "   - Frontend: app/frontend/src/"
	@echo ""
	@echo "🔧 実行順序:"
	@echo "   1. Python: ruff fix (import整形 & lint自動修正)"
	@echo "   2. Python: black format (コード整形)"
	@echo "   3. Frontend: prettier write (コード整形)"
	@echo "   4. Frontend: eslint fix (lint自動修正)"
	@echo ""
	@read -p "続行しますか？ [y/N] " confirm; \
	if [ "$$confirm" != "y" ] && [ "$$confirm" != "Y" ]; then \
		echo "❌ キャンセルされました"; \
		exit 1; \
	fi
	@echo ""
	@echo "============================================================"
	@echo "▶️  Step 1/4: Python ruff fix"
	@echo "============================================================"
	@$(MAKE) --no-print-directory fmt-python-ruff
	@echo ""
	@echo "============================================================"
	@echo "▶️  Step 2/4: Python black format"
	@echo "============================================================"
	@$(MAKE) --no-print-directory fmt-python-black
	@echo ""
	@echo "============================================================"
	@echo "▶️  Step 3/4: Frontend prettier write"
	@echo "============================================================"
	@$(MAKE) --no-print-directory fmt-frontend-prettier
	@echo ""
	@echo "============================================================"
	@echo "▶️  Step 4/4: Frontend eslint fix"
	@echo "============================================================"
	@$(MAKE) --no-print-directory fmt-frontend-eslint
	@echo ""
	@echo "============================================================"
	@echo "✅ 初回一括整形が完了しました！"
	@echo "============================================================"
	@echo ""
	@echo "📋 次のステップ:"
	@echo "   1. git status で変更を確認"
	@echo "   2. git add -A で変更をステージング"
	@echo "   3. git commit -m 'chore: apply initial formatting (ruff, black, prettier, eslint)'"
	@echo "   4. git push でリモートにプッシュ"
	@echo ""
	@echo "🔍 変更のチェック:"
	@echo "   make check-format  # 整形が正しく適用されたか確認"
	@echo ""

# ============================================================
# Python整形（分割実行可能）
# ============================================================
fmt-python: ## 🐍 Python全体を整形（ruff → black の順）
	@$(MAKE) --no-print-directory fmt-python-ruff
	@$(MAKE) --no-print-directory fmt-python-black

fmt-python-ruff: ## 🔧 Python ruff fix（import整形 & lint自動修正）
	@echo "🔧 Python ruff fix を実行中..."
	@nice -n 10 pre-commit run ruff --all-files || true
	@echo "✅ ruff fix 完了"

fmt-python-black: ## 🎨 Python black format（コード整形）
	@echo "🎨 Python black format を実行中..."
	@nice -n 10 pre-commit run black --all-files
	@echo "✅ black format 完了"

# ============================================================
# Frontend整形（分割実行可能）
# ============================================================
fmt-frontend: ## 💎 Frontend全体を整形（prettier → eslint の順）
	@$(MAKE) --no-print-directory fmt-frontend-prettier
	@$(MAKE) --no-print-directory fmt-frontend-eslint

fmt-frontend-prettier: ## 💅 Frontend prettier write（コード整形）
	@echo "💅 Frontend prettier write を実行中..."
	@cd app/frontend && nice -n 10 npm run format
	@echo "✅ prettier write 完了"

fmt-frontend-eslint: ## 🔍 Frontend eslint fix（lint自動修正）
	@echo "🔍 Frontend eslint fix を実行中..."
	@cd app/frontend && nice -n 10 npm run lint:fix || true
	@echo "✅ eslint fix 完了"

# ============================================================
# チェックのみ（修正しない）
# ============================================================
check-format: ## 🔍 全体の整形チェック（修正なし）
	@echo "============================================================"
	@echo "🔍 整形チェックを実行します（修正はしません）"
	@echo "============================================================"
	@$(MAKE) --no-print-directory check-python
	@$(MAKE) --no-print-directory check-frontend
	@echo "============================================================"
	@echo "✅ 整形チェック完了"
	@echo "============================================================"

check-python: ## 🐍 Python整形チェック（ruff + black）
	@echo "▶️  Python ruff check..."
	@pre-commit run ruff --all-files || echo "⚠️  ruff にエラーがあります"
	@echo ""
	@echo "▶️  Python black check..."
	@pre-commit run black --all-files || echo "⚠️  black にエラーがあります"

check-frontend: ## 💎 Frontend整形チェック（prettier + eslint）
	@echo "▶️  Frontend prettier check..."
	@cd app/frontend && npm run format:check || echo "⚠️  prettier にエラーがあります"
	@echo ""
	@echo "▶️  Frontend eslint check..."
	@cd app/frontend && npm run lint || echo "⚠️  eslint にエラーがあります"

# ============================================================
# Step-by-Step Formatting（WSL推奨）
# ============================================================
# scripts/format_step_by_step.sh を使用
# pre-commit run --all-files を避けてCPU負荷を軽減
# ============================================================
fmt-step-all: ## 🚀 【WSL推奨】全処理をステップ実行（CPU負荷軽減）
	@bash scripts/format_step_by_step.sh all

fmt-step-py-fix: ## 🐍 Python ruff --fix のみ
	@bash scripts/format_step_by_step.sh python-fix

fmt-step-py: ## 🎨 Python black format のみ
	@bash scripts/format_step_by_step.sh python-format

fmt-step-fe: ## 💅 Frontend prettier --write のみ
	@bash scripts/format_step_by_step.sh frontend-format

fmt-step-fe-fix: ## 🔍 Frontend eslint --fix のみ
	@bash scripts/format_step_by_step.sh frontend-fix

fmt-step-check: ## 🔍 全チェック（修正なし、ステップ実行版）
	@bash scripts/format_step_by_step.sh check

# ============================================================
# Type Checking（段階的型チェック）
# ============================================================
# mypy による静的型チェック
# - 最初は core/ と api/ のみ対象（段階導入）
# - infra/, config/ は後回し
# - 設定: app/backend/core_api/pyproject.toml の [tool.mypy]
# ============================================================
.PHONY: typecheck typecheck-core typecheck-api typecheck-all

typecheck: typecheck-core ## 🔬 型チェック（core層のみ、段階導入）
	@echo "✅ 型チェック完了"

typecheck-core: ## 🔬 core層の型チェック（ドメイン/ユースケース）
	@echo "============================================================"
	@echo "🔬 Type Check: core層（ドメイン/ユースケース）"
	@echo "============================================================"
	@docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T core_api \
		mypy app/core --config-file=/backend/pyproject.toml || true
	@echo ""

typecheck-api: ## 🔬 api層の型チェック（ルーター/エンドポイント）
	@echo "============================================================"
	@echo "🔬 Type Check: api層（ルーター/エンドポイント）"
	@echo "============================================================"
	@docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T core_api \
		mypy app/api --config-file=/backend/pyproject.toml || true
	@echo ""

typecheck-all: ## 🔬 全体の型チェック（将来用、現時点では非推奨）
	@echo "============================================================"
	@echo "🔬 Type Check: 全体（core + api + infra）"
	@echo "============================================================"
	@echo "⚠️  注意: 現在は段階導入中のため、多くのエラーが出る可能性があります"
	@docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T core_api \
		mypy app --config-file=/backend/pyproject.toml || true
	@echo ""

# ============================================================
# Safe Check（WSL2 フリーズ防止）
# ============================================================
# scripts/safe_check.sh を使用して安全にチェック実行
# 危険なコマンド（全体スキャン）を自動でブロック
# ============================================================
.PHONY: check-light check-ci check-safe

check-light: ## 🔍 軽量チェック（差分のみ、WSL2安全）
	@echo "============================================================"
	@echo "🔍 軽量チェック（staged ファイルのみ）"
	@echo "============================================================"
	@bash scripts/safe_check.sh staged

check-safe-python: ## 🐍 Python チェック（WSL2安全）
	@bash scripts/safe_check.sh python

check-safe-frontend: ## 💎 Frontend チェック（WSL2安全）
	@bash scripts/safe_check.sh frontend

check-safe-typecheck: ## 🔬 型チェック（WSL2安全）
	@bash scripts/safe_check.sh typecheck

check-ci: ## 🚨 CI専用チェック（ローカルで実行しない）
	@echo "============================================================"
	@echo "⚠️  警告: CI専用のチェックです"
	@echo "============================================================"
	@echo ""
	@echo "このコマンドは GitHub Actions で実行されます。"
	@echo "ローカルで全体チェックを実行すると、WSL2 環境で"
	@echo "フリーズする可能性があります。"
	@echo ""
	@echo "代わりに以下を使用してください:"
	@echo "  make fmt-step-all      # 全体整形（直列・対象限定）"
	@echo "  make fmt-step-check    # 全体チェック（修正なし）"
	@echo "  make check-light       # 差分のみチェック"
	@echo ""
	@read -p "本当に実行しますか？ [y/N] " confirm; \
	if [ "$$confirm" != "y" ] && [ "$$confirm" != "Y" ]; then \
		echo "❌ キャンセルされました"; \
		exit 1; \
	fi
	@echo ""
	@echo "⚠️  全体チェック実行中..."
	@$(MAKE) --no-print-directory check-format
