#!/bin/bash
# =============================================================================
# 出力ユーティリティ - Git フック用の共通出力関数
# =============================================================================

# =============================================================================
# 色定義
# =============================================================================
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly MAGENTA='\033[0;35m'
readonly BOLD='\033[1m'
readonly NC='\033[0m'  # No Color

# =============================================================================
# 出力関数
# =============================================================================

# エラーメッセージ
log_error() {
    echo -e "${RED}❌ エラー: $*${NC}" >&2
}

# 警告メッセージ
log_warn() {
    echo -e "${YELLOW}⚠️  警告: $*${NC}" >&2
}

# 成功メッセージ
log_success() {
    echo -e "${GREEN}✅ $*${NC}"
}

# 情報メッセージ
log_info() {
    echo -e "${BLUE}ℹ️  $*${NC}"
}

# 処理中メッセージ
log_processing() {
    echo -e "${CYAN}🔍 $*${NC}"
}

# セクションヘッダー
log_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}$*${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# エラーセクション（赤）
log_error_section() {
    echo ""
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}${BOLD}$*${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# ファイル名表示（強調）
log_file() {
    echo -e "   ${YELLOW}$*${NC}"
}

# チェック項目の開始
log_check() {
    local step="$1"
    local total="$2"
    local message="$3"
    echo -e "${CYAN}🔍 [$step/$total] $message${NC}"
}

# プログレスバー（簡易版）
show_progress() {
    local current="$1"
    local total="$2"
    local width=50
    local percentage=$((current * 100 / total))
    local filled=$((width * current / total))

    printf "\r${CYAN}["
    printf "%${filled}s" | tr ' ' '='
    printf "%$((width - filled))s" | tr ' ' ' '
    printf "] %3d%% (%d/%d)${NC}" "$percentage" "$current" "$total"

    if [ "$current" -eq "$total" ]; then
        echo ""
    fi
}

# =============================================================================
# インタラクティブ確認
# =============================================================================

# Yes/No 確認（デフォルト No）
confirm_action() {
    local message="$1"
    echo -e "${YELLOW}${message} (y/N): ${NC}"
    read -r response
    [[ "$response" =~ ^[Yy]$ ]]
}

# Yes/No 確認（デフォルト Yes）
confirm_action_default_yes() {
    local message="$1"
    echo -e "${YELLOW}${message} (Y/n): ${NC}"
    read -r response
    [[ ! "$response" =~ ^[Nn]$ ]]
}

# =============================================================================
# エラー詳細表示
# =============================================================================

# 機密ファイル検出時の詳細表示
show_forbidden_file_details() {
    local file="$1"

    log_error_section "機密ファイルが検出されました"
    log_file "$file"
    echo ""
    echo "このファイルは以下の理由で Git 管理外にすべきです:"

    case "$file" in
        env/.env.*)
            echo "  • 環境変数ファイル（環境固有の設定を含む）"
            ;;
        secrets/*.secrets)
            echo "  • 機密情報ファイル（パスワード、API キー等）"
            ;;
        secrets/gcp-sa*.json)
            echo "  • GCP サービスアカウントキー（認証情報）"
            ;;
        *.pem|*.key)
            echo "  • 秘密鍵ファイル（暗号化キー）"
            ;;
        *.dump)
            echo "  • データベースダンプ（個人情報を含む可能性）"
            ;;
    esac

    echo ""
    echo "対応方法:"
    echo "  1. ファイルを unstage する:"
    echo "     ${CYAN}git restore --staged $file${NC}"
    echo ""
    echo "  2. .gitignore が正しく設定されているか確認:"
    echo "     ${CYAN}git check-ignore -v $file${NC}"
    echo ""
}

# 機密情報パターン検出時の詳細表示
show_sensitive_content_details() {
    local file="$1"
    local pattern="$2"
    local matched_lines="$3"

    log_error_section "機密情報パターンが検出されました"
    echo "ファイル: $(log_file "$file")"
    echo "パターン: $pattern"
    echo ""
    echo "該当箇所:"
    echo "$matched_lines" | head -5 | while IFS= read -r line; do
        echo "  ${YELLOW}$line${NC}"
    done

    local line_count
    line_count=$(echo "$matched_lines" | wc -l)
    if [ "$line_count" -gt 5 ]; then
        echo "  ... (他 $((line_count - 5)) 行)"
    fi
    echo ""
}

# =============================================================================
# ヘルプメッセージ表示
# =============================================================================

show_commit_help() {
    log_section "Git Commit のベストプラクティス"
    echo ""
    echo "✓ 許可されるファイル:"
    echo "  • env/.env.example, env/*.template"
    echo "  • secrets/*.template, secrets/README.md"
    echo "  • config/ 配下の設定ファイル"
    echo ""
    echo "✗ 禁止されるファイル:"
    echo "  • env/.env.* （テンプレート以外）"
    echo "  • secrets/*.secrets"
    echo "  • *.pem, *.key （秘密鍵）"
    echo "  • gcp-sa*.json （GCP キー）"
    echo ""
}

show_push_help() {
    log_section "リモートプッシュ前の確認事項"
    echo ""
    echo "1. 機密ファイルが履歴に含まれていないか"
    echo "2. パスワードや API キーがコミットされていないか"
    echo "3. .gitignore が正しく設定されているか"
    echo ""
    echo "問題が見つかった場合:"
    echo "  ${CYAN}bash scripts/git/cleanup_git_history.sh${NC}"
    echo ""
}

# =============================================================================
# エクスポート
# =============================================================================
export -f log_error
export -f log_warn
export -f log_success
export -f log_info
export -f log_processing
export -f log_section
export -f log_error_section
export -f log_file
export -f log_check
export -f show_progress
export -f confirm_action
export -f confirm_action_default_yes
export -f show_forbidden_file_details
export -f show_sensitive_content_details
export -f show_commit_help
export -f show_push_help
