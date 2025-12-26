#!/bin/bash
# =============================================================================
# 共通ユーティリティ関数ライブラリ
# =============================================================================
# 全てのスクリプトから利用できる共通関数を提供
#
# 使用方法:
#   source "$(dirname "$0")/lib/common.sh"

# エラー時に即座に終了
set -euo pipefail

# =============================================================================
# 色定義
# =============================================================================
export RED='\033[0;31m'
export GREEN='\033[0;32m'
export YELLOW='\033[1;33m'
export BLUE='\033[0;34m'
export CYAN='\033[0;36m'
export MAGENTA='\033[0;35m'
export NC='\033[0m' # No Color

# =============================================================================
# ログ出力関数
# =============================================================================

# 情報メッセージ
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

# 成功メッセージ
log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

# 警告メッセージ
log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

# エラーメッセージ
log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

# デバッグメッセージ（DEBUG=1 の時のみ表示）
log_debug() {
    if [[ "${DEBUG:-0}" == "1" ]]; then
        echo -e "${CYAN}[DEBUG]${NC} $*" >&2
    fi
}

# セクション開始
log_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$*${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# ステップ表示
log_step() {
    echo -e "${GREEN}▶${NC} $*"
}

# チェック成功
log_check_ok() {
    echo -e "  ${GREEN}✓${NC} $*"
}

# チェック警告
log_check_warn() {
    echo -e "  ${YELLOW}○${NC} $*"
}

# チェック失敗
log_check_fail() {
    echo -e "  ${RED}✗${NC} $*"
}

# =============================================================================
# ファイル・ディレクトリ操作
# =============================================================================

# Git リポジトリのルートを取得
get_repo_root() {
    git rev-parse --show-toplevel 2>/dev/null || {
        log_error "Git リポジトリではありません"
        return 1
    }
}

# スクリプトのディレクトリを取得
get_script_dir() {
    cd "$(dirname "${BASH_SOURCE[0]}")" && pwd
}

# ファイルが存在するかチェック
check_file_exists() {
    local file="$1"
    if [[ ! -f "$file" ]]; then
        log_error "ファイルが見つかりません: $file"
        return 1
    fi
    return 0
}

# ディレクトリが存在するかチェック
check_dir_exists() {
    local dir="$1"
    if [[ ! -d "$dir" ]]; then
        log_error "ディレクトリが見つかりません: $dir"
        return 1
    fi
    return 0
}

# =============================================================================
# ユーザー確認
# =============================================================================

# yes/no 確認
confirm() {
    local prompt="${1:-続行しますか?}"
    local default="${2:-no}"

    if [[ "$default" == "yes" ]]; then
        prompt="$prompt (Y/n)"
        local pattern="^[Nn]"
    else
        prompt="$prompt (y/N)"
        local pattern="^[Yy]"
    fi

    echo -e "${YELLOW}$prompt${NC}"
    read -r response

    if [[ "$default" == "yes" ]]; then
        # デフォルトが yes の場合、N/n 以外は yes
        [[ ! "$response" =~ $pattern ]]
    else
        # デフォルトが no の場合、Y/y のみ yes
        [[ "$response" =~ $pattern ]]
    fi
}

# 重要な確認（"yes" の入力を要求）
confirm_critical() {
    local prompt="$1"
    echo -e "${RED}⚠️  重要: $prompt${NC}"
    echo -e "${RED}本当に実行しますか? (yes と入力)${NC}"
    read -r response
    [[ "$response" == "yes" ]]
}

# =============================================================================
# コマンド存在確認
# =============================================================================

# コマンドが存在するかチェック
check_command() {
    local cmd="$1"
    if ! command -v "$cmd" &> /dev/null; then
        log_error "コマンドが見つかりません: $cmd"
        return 1
    fi
    return 0
}

# 必須コマンドの確認（複数）
require_commands() {
    local missing=()
    for cmd in "$@"; do
        if ! command -v "$cmd" &> /dev/null; then
            missing+=("$cmd")
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "以下のコマンドがインストールされていません:"
        for cmd in "${missing[@]}"; do
            log_error "  - $cmd"
        done
        return 1
    fi
    return 0
}

# =============================================================================
# バックアップ
# =============================================================================

# ディレクトリ/ファイルのバックアップを作成
create_backup() {
    local target="$1"
    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_name="${target}_backup_${timestamp}"

    if [[ -e "$target" ]]; then
        log_step "バックアップを作成中: $backup_name"
        cp -r "$target" "$backup_name"
        log_success "バックアップ作成完了: $backup_name"
        echo "$backup_name"
    else
        log_error "バックアップ対象が見つかりません: $target"
        return 1
    fi
}

# tar.gz バックアップを作成
create_tar_backup() {
    local target="$1"
    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_name="${target##*/}_backup_${timestamp}.tar.gz"

    if [[ -e "$target" ]]; then
        log_step "tar.gz バックアップを作成中: $backup_name"
        tar -czf "$backup_name" "$target"
        log_success "バックアップ作成完了: $backup_name"
        echo "$backup_name"
    else
        log_error "バックアップ対象が見つかりません: $target"
        return 1
    fi
}

# =============================================================================
# Git 操作
# =============================================================================

# Git の変更があるかチェック
check_git_clean() {
    if [[ -n "$(git status --porcelain)" ]]; then
        log_warn "Git に未コミットの変更があります"
        git status --short
        return 1
    fi
    return 0
}

# 現在のブランチを取得
get_current_branch() {
    git rev-parse --abbrev-ref HEAD
}

# リモート URL を取得
get_remote_url() {
    local remote="${1:-origin}"
    git remote get-url "$remote" 2>/dev/null
}

# =============================================================================
# 環境変数ファイル操作
# =============================================================================

# .env ファイルから変数を読み込む
load_env_file() {
    local env_file="$1"
    check_file_exists "$env_file" || return 1

    log_debug ".env ファイルを読み込み中: $env_file"

    # コメントと空行を除外して読み込み
    while IFS= read -r line; do
        # コメント行と空行をスキップ
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        [[ -z "$line" ]] && continue

        # エクスポート
        if [[ "$line" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)= ]]; then
            # shellcheck disable=SC2163
            export "$line"
            log_debug "  loaded: ${BASH_REMATCH[1]}"
        fi
    done < "$env_file"
}

# .env ファイルから特定の変数を取得
get_env_var() {
    local env_file="$1"
    local var_name="$2"
    local default_value="${3:-}"

    check_file_exists "$env_file" || {
        echo "$default_value"
        return 1
    }

    local value
    value=$(grep "^${var_name}=" "$env_file" | cut -d'=' -f2- | tr -d '"' | tr -d "'")
    echo "${value:-$default_value}"
}

# =============================================================================
# 配列操作
# =============================================================================

# 配列に要素が含まれているかチェック
array_contains() {
    local element="$1"
    shift
    local array=("$@")

    for item in "${array[@]}"; do
        [[ "$item" == "$element" ]] && return 0
    done
    return 1
}

# =============================================================================
# エラーハンドリング
# =============================================================================

# エラートラップ設定
setup_error_trap() {
    trap 'handle_error $? $LINENO' ERR
}

# エラーハンドラ
handle_error() {
    local exit_code=$1
    local line_number=$2
    log_error "スクリプトがエラーで終了しました (終了コード: $exit_code, 行: $line_number)"
    exit "$exit_code"
}

# クリーンアップ関数の登録
register_cleanup() {
    local cleanup_func="$1"
    # shellcheck disable=SC2064
    trap "$cleanup_func" EXIT
}

# =============================================================================
# バージョン比較
# =============================================================================

# バージョン比較（version1 >= version2 なら 0 を返す）
version_gte() {
    local version1="$1"
    local version2="$2"

    # sort -V で比較
    if [[ "$(printf '%s\n' "$version2" "$version1" | sort -V | head -n1)" == "$version2" ]]; then
        return 0
    fi
    return 1
}

# =============================================================================
# 初期化
# =============================================================================

# スクリプトのヘッダー表示
show_script_header() {
    local script_name="$1"
    local description="$2"

    log_section "🚀 $script_name"
    if [[ -n "$description" ]]; then
        log_info "$description"
        echo ""
    fi
}

# 初期化完了メッセージ
log_init_complete() {
    log_debug "共通ライブラリの初期化が完了しました"
}

# =============================================================================
# 初期化実行
# =============================================================================
log_init_complete
