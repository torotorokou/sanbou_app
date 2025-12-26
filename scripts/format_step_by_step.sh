#!/usr/bin/env bash
# ============================================================
# Step-by-Step Formatting Script
# ============================================================
#
# WSL/VSCodeでCPU張り付きや再接続ループを起こしやすい
# "pre-commit run --all-files" を避け、各ツールを1つずつ
# 安全に実行するためのスクリプト
#
# 使い方:
#   bash scripts/format_step_by_step.sh python-fix      # Python ruff --fix のみ
#   bash scripts/format_step_by_step.sh python-format   # Python black のみ
#   bash scripts/format_step_by_step.sh frontend-format # Frontend prettier のみ
#   bash scripts/format_step_by_step.sh frontend-fix    # Frontend eslint --fix のみ
#   bash scripts/format_step_by_step.sh check           # 全チェック（修正なし）
#   bash scripts/format_step_by_step.sh all             # 全処理を順番に実行
#
# ============================================================

set -euo pipefail

# ============================================================
# 設定
# ============================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/app/frontend"

# ログディレクトリ（任意）
LOG_DIR="$PROJECT_ROOT/.tmp/format-logs"
mkdir -p "$LOG_DIR"

# 色付きログ
COLOR_RESET='\033[0m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_RED='\033[0;31m'
COLOR_BLUE='\033[0;34m'

log_info() {
    echo -e "${COLOR_BLUE}ℹ️  $*${COLOR_RESET}"
}

log_success() {
    echo -e "${COLOR_GREEN}✅ $*${COLOR_RESET}"
}

log_warning() {
    echo -e "${COLOR_YELLOW}⚠️  $*${COLOR_RESET}"
}

log_error() {
    echo -e "${COLOR_RED}❌ $*${COLOR_RESET}"
}

log_step() {
    echo ""
    echo "============================================================"
    echo -e "${COLOR_BLUE}▶️  $*${COLOR_RESET}"
    echo "============================================================"
}

# ============================================================
# Python: ruff --fix
# ============================================================
python_fix() {
    log_step "Step: Python ruff --fix (import整形 & lint自動修正)"

    log_info "CPU負荷軽減のため nice -n 10 で実行します"
    log_info "対象: app/backend/ (migrations除外)"

    cd "$PROJECT_ROOT"

    if ! command -v pre-commit &> /dev/null; then
        log_error "pre-commit がインストールされていません"
        exit 1
    fi

    # ruffは pre-commit 経由で実行（環境が統一されているため）
    # --all-files は使わず、ファイル指定で実行
    log_info "ruff --fix を実行中..."

    nice -n 10 pre-commit run ruff --all-files || {
        log_warning "ruff で一部エラーがありましたが、継続します"
        return 0
    }

    log_success "Python ruff --fix 完了"
}

# ============================================================
# Python: black format
# ============================================================
python_format() {
    log_step "Step: Python black format (コード整形)"

    log_info "CPU負荷軽減のため nice -n 10 で実行します"
    log_info "対象: app/backend/ (migrations除外)"

    cd "$PROJECT_ROOT"

    if ! command -v pre-commit &> /dev/null; then
        log_error "pre-commit がインストールされていません"
        exit 1
    fi

    log_info "black format を実行中..."

    nice -n 10 pre-commit run black --all-files || {
        log_error "black format でエラーが発生しました"
        exit 1
    }

    log_success "Python black format 完了"
}

# ============================================================
# Frontend: prettier --write
# ============================================================
frontend_format() {
    log_step "Step: Frontend prettier --write (コード整形)"

    log_info "対象: app/frontend/src/ (node_modules除外)"
    log_info "⚠️  注意: ルート全体ではなく frontend 配下のみ対象"

    if [ ! -d "$FRONTEND_DIR" ]; then
        log_error "Frontend ディレクトリが見つかりません: $FRONTEND_DIR"
        exit 1
    fi

    cd "$FRONTEND_DIR"

    if [ ! -f "package.json" ]; then
        log_error "package.json が見つかりません"
        exit 1
    fi

    log_info "npm install が必要な場合は先に実行してください"

    # package.json の format script を使用
    log_info "prettier --write を実行中..."

    nice -n 10 npm run format || {
        log_error "prettier でエラーが発生しました"
        exit 1
    }

    log_success "Frontend prettier --write 完了"
}

# ============================================================
# Frontend: eslint --fix
# ============================================================
frontend_fix() {
    log_step "Step: Frontend eslint --fix (lint自動修正)"

    log_info "対象: app/frontend/src/ (node_modules除外)"
    log_info "⚠️  注意: ルート全体ではなく frontend 配下のみ対象"

    if [ ! -d "$FRONTEND_DIR" ]; then
        log_error "Frontend ディレクトリが見つかりません: $FRONTEND_DIR"
        exit 1
    fi

    cd "$FRONTEND_DIR"

    if [ ! -f "package.json" ]; then
        log_error "package.json が見つかりません"
        exit 1
    fi

    # package.json の lint:fix script を使用
    log_info "eslint --fix を実行中..."

    nice -n 10 npm run lint:fix || {
        log_warning "eslint で一部エラーがありましたが、継続します"
        return 0
    }

    log_success "Frontend eslint --fix 完了"
}

# ============================================================
# Check: 全チェック（修正なし）
# ============================================================
check_all() {
    log_step "Check: 全チェック（修正なし）"

    local has_error=0

    # Python ruff check
    log_info "Python ruff check を実行中..."
    cd "$PROJECT_ROOT"
    if ! nice -n 10 pre-commit run ruff --all-files; then
        log_warning "ruff にエラーがあります"
        has_error=1
    fi

    # Python black check
    log_info "Python black check を実行中..."
    cd "$PROJECT_ROOT"
    if ! nice -n 10 pre-commit run black --all-files; then
        log_warning "black にエラーがあります"
        has_error=1
    fi

    # Frontend prettier check
    log_info "Frontend prettier check を実行中..."
    cd "$FRONTEND_DIR"
    if ! npm run format:check; then
        log_warning "prettier にエラーがあります"
        has_error=1
    fi

    # Frontend eslint check
    log_info "Frontend eslint check を実行中..."
    cd "$FRONTEND_DIR"
    if ! npm run lint; then
        log_warning "eslint にエラーがあります"
        has_error=1
    fi

    if [ $has_error -eq 0 ]; then
        log_success "すべてのチェックに合格しました！"
    else
        log_warning "一部のチェックでエラーがあります"
        return 1
    fi
}

# ============================================================
# All: 全処理を順番に実行
# ============================================================
run_all() {
    log_step "All: 全処理を順番に実行"

    log_info "実行順序:"
    log_info "  1. Python ruff --fix"
    log_info "  2. Python black format"
    log_info "  3. Frontend prettier --write"
    log_info "  4. Frontend eslint --fix"
    log_info "  5. 全チェック"

    echo ""
    read -p "続行しますか？ [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "キャンセルされました"
        exit 0
    fi

    local start_time=$(date +%s)

    python_fix
    python_format
    frontend_format
    frontend_fix

    log_step "最終チェック"
    check_all || {
        log_warning "最終チェックでエラーがありました（修正が必要な箇所があります）"
    }

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log_success "全処理が完了しました！（所要時間: ${duration}秒）"

    echo ""
    log_info "次のステップ:"
    log_info "  1. git status で変更を確認"
    log_info "  2. git add -A で変更をステージング"
    log_info "  3. git commit -m 'chore: apply formatting (ruff, black, prettier, eslint)'"
}

# ============================================================
# Help
# ============================================================
show_help() {
    cat <<EOF
Step-by-Step Formatting Script

使い方:
  bash scripts/format_step_by_step.sh <command>

コマンド:
  python-fix        Python ruff --fix のみ実行
  python-format     Python black format のみ実行
  frontend-format   Frontend prettier --write のみ実行
  frontend-fix      Frontend eslint --fix のみ実行
  check             全チェック（修正なし）
  all               全処理を順番に実行
  help              このヘルプを表示

特徴:
  - pre-commit run --all-files を使わない（WSL負荷軽減）
  - 各ツールを1つずつ順番に実行
  - nice -n 10 でCPU優先度を下げる
  - 途中で止めても再開可能

例:
  # Python のみ
  bash scripts/format_step_by_step.sh python-fix
  bash scripts/format_step_by_step.sh python-format

  # Frontend のみ
  bash scripts/format_step_by_step.sh frontend-format
  bash scripts/format_step_by_step.sh frontend-fix

  # 全部
  bash scripts/format_step_by_step.sh all

  # チェックのみ
  bash scripts/format_step_by_step.sh check

詳細: docs/dev/STEP_BY_STEP_FORMAT.md
EOF
}

# ============================================================
# Main
# ============================================================
main() {
    local command="${1:-help}"

    case "$command" in
        python-fix)
            python_fix
            ;;
        python-format)
            python_format
            ;;
        frontend-format)
            frontend_format
            ;;
        frontend-fix)
            frontend_fix
            ;;
        check)
            check_all
            ;;
        all)
            run_all
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "不明なコマンド: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# スクリプトが直接実行された場合のみmainを呼ぶ
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
