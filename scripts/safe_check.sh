#!/usr/bin/env bash
# ============================================================
# safe_check.sh - WSL2でフリーズさせない安全なチェック実行
# ============================================================
#
# 目的:
#   VSCode Remote-WSL でのフリーズ/再接続ループを防ぐため、
#   危険なコマンド（全体スキャン）を実行させずに誘導する
#
# 危険な操作:
#   ❌ pre-commit run --all-files（全体スキャン）
#   ❌ eslint .（リポジトリルートから）
#   ❌ prettier .（リポジトリルートから）
#   ❌ ruff check .（全体）
#
# 安全な代替:
#   ✅ make fmt-step-all（直列・対象限定）
#   ✅ pre-commit run（stagedのみ）
#   ✅ CI で全体チェック
#
# ============================================================

set -euo pipefail

# 色定義
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================
# ヘルプメッセージ
# ============================================================
show_help() {
    cat <<EOF
${BLUE}============================================================${NC}
${BLUE}safe_check.sh - WSL2 フリーズ防止チェッカー${NC}
${BLUE}============================================================${NC}

${GREEN}使い方:${NC}
  bash scripts/safe_check.sh <command>

${GREEN}安全なコマンド:${NC}
  ${BLUE}staged${NC}         - pre-commit run（stagedファイルのみ）
  ${BLUE}python${NC}         - Python のみ整形チェック
  ${BLUE}frontend${NC}       - Frontend のみ整形チェック
  ${BLUE}typecheck${NC}      - 型チェック（対象限定）
  ${BLUE}help${NC}           - このヘルプを表示

${YELLOW}⚠️  禁止コマンド（フリーズの原因）:${NC}
  ${RED}❌ pre-commit run --all-files${NC}
  ${RED}❌ eslint .${NC}
  ${RED}❌ prettier .${NC}
  ${RED}❌ ruff check .${NC}

${GREEN}推奨する実行方法:${NC}
  ${BLUE}初回整形:${NC}
    make fmt-step-all        # 直列・対象限定で安全に実行

  ${BLUE}日常のチェック:${NC}
    bash scripts/safe_check.sh staged     # コミット前チェック
    make fmt-step-check                   # 全体チェック（修正なし）

  ${BLUE}全体チェック:${NC}
    CI に任せる（GitHub Actions で実行）

${BLUE}============================================================${NC}
${BLUE}📖 詳細: docs/dev/SAFE_BOOTSTRAP_FORMAT.md${NC}
${BLUE}============================================================${NC}
EOF
}

# ============================================================
# 危険なコマンドの検出とブロック
# ============================================================
block_dangerous_commands() {
    # 環境変数チェック（pre-commit run --all-files の検出）
    if [[ "${SKIP_PRE_COMMIT_ALL_FILES_CHECK:-}" != "true" ]]; then
        if [[ "${PRE_COMMIT_FROM_REF:-}" != "" ]] || [[ "${PRE_COMMIT_TO_REF:-}" != "" ]]; then
            # pre-commit run --all-files が実行されている可能性
            if [[ "${PRE_COMMIT_ALL_FILES:-}" == "1" ]]; then
                echo -e "${RED}============================================================${NC}"
                echo -e "${RED}❌ エラー: pre-commit run --all-files は禁止されています${NC}"
                echo -e "${RED}============================================================${NC}"
                echo ""
                echo -e "${YELLOW}理由:${NC}"
                echo "  WSL2 環境で全体スキャンを実行すると、CPU 張り付きで"
                echo "  VSCode Remote-WSL が再接続ループに陥る可能性があります。"
                echo ""
                echo -e "${GREEN}代替方法:${NC}"
                echo "  1) staged ファイルのみチェック:"
                echo "     ${BLUE}pre-commit run${NC}  （--all-files なし）"
                echo ""
                echo "  2) 初回の全体整形:"
                echo "     ${BLUE}make fmt-step-all${NC}"
                echo ""
                echo "  3) CI で全体チェック:"
                echo "     GitHub Actions が自動実行します"
                echo ""
                echo -e "${YELLOW}⚠️  どうしても実行する場合:${NC}"
                echo "     ${BLUE}SKIP_PRE_COMMIT_ALL_FILES_CHECK=true pre-commit run --all-files${NC}"
                echo "     ※ 自己責任で実行してください（フリーズの可能性あり）"
                echo ""
                exit 1
            fi
        fi
    fi

    # コマンドライン引数チェック（eslint . / prettier . の検出）
    for arg in "$@"; do
        case "$arg" in
            "--all-files")
                echo -e "${RED}❌ エラー: --all-files オプションは禁止されています${NC}"
                echo ""
                echo -e "${GREEN}代替方法: make fmt-step-all${NC}"
                exit 1
                ;;
        esac
    done
}

# ============================================================
# 安全なチェック実行
# ============================================================
run_safe_check() {
    local command="${1:-help}"

    case "$command" in
        staged)
            echo -e "${GREEN}============================================================${NC}"
            echo -e "${GREEN}✅ Staged ファイルのみチェック（安全）${NC}"
            echo -e "${GREEN}============================================================${NC}"
            echo ""

            # nice で優先度を下げて実行（CPU負荷軽減）
            if command -v nice &> /dev/null; then
                nice -n 10 pre-commit run
            else
                pre-commit run
            fi
            ;;

        python)
            echo -e "${GREEN}============================================================${NC}"
            echo -e "${GREEN}✅ Python のみチェック（安全）${NC}"
            echo -e "${GREEN}============================================================${NC}"
            echo ""
            make check-python
            ;;

        frontend)
            echo -e "${GREEN}============================================================${NC}"
            echo -e "${GREEN}✅ Frontend のみチェック（安全）${NC}"
            echo -e "${GREEN}============================================================${NC}"
            echo ""
            make check-frontend
            ;;

        typecheck)
            echo -e "${GREEN}============================================================${NC}"
            echo -e "${GREEN}✅ 型チェック（対象限定・安全）${NC}"
            echo -e "${GREEN}============================================================${NC}"
            echo ""
            make typecheck
            ;;

        help|--help|-h)
            show_help
            ;;

        *)
            echo -e "${RED}❌ エラー: 不明なコマンド '$command'${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# ============================================================
# メイン処理
# ============================================================
main() {
    # 危険なコマンドをブロック
    block_dangerous_commands "$@"

    # 安全なチェックを実行
    run_safe_check "$@"
}

# スクリプト実行
main "$@"
