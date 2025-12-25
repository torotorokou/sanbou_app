#!/bin/bash
# =============================================================================
# Git 操作専用ライブラリ
# =============================================================================
# Git フック、履歴操作、セキュリティチェックなどの共通関数

# 共通ライブラリの読み込み
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

# =============================================================================
# Git フック管理
# =============================================================================

# Git フックのリスト
declare -a GIT_HOOKS=(
    "pre-commit"
    "pre-push"
    "commit-msg"
    "prepare-commit-msg"
)

# Git フックが存在するかチェック
check_hook_exists() {
    local hook_name="$1"
    local repo_root
    repo_root=$(get_repo_root) || return 1
    local hook_path="${repo_root}/.git/hooks/${hook_name}"

    [[ -f "$hook_path" ]] && [[ -x "$hook_path" ]]
}

# 全ての Git フックをチェック
check_all_hooks() {
    local repo_root
    repo_root=$(get_repo_root) || return 1
    local all_ok=0

    log_step "Git フックの状態を確認中..."

    for hook in "${GIT_HOOKS[@]}"; do
        if check_hook_exists "$hook"; then
            log_check_ok "$hook は既にインストール済み"
        else
            log_check_warn "$hook はインストールされていません"
            all_ok=1
        fi
    done

    return $all_ok
}

# Git フックに実行権限を付与
set_hook_executable() {
    local hook_name="$1"
    local repo_root
    repo_root=$(get_repo_root) || return 1
    local hook_path="${repo_root}/.git/hooks/${hook_name}"

    if [[ -f "$hook_path" ]]; then
        chmod +x "$hook_path"
        log_debug "実行権限を付与: $hook_name"
        return 0
    else
        log_warn "フックが見つかりません: $hook_name"
        return 1
    fi
}

# 全ての Git フックに実行権限を付与
set_all_hooks_executable() {
    local repo_root
    repo_root=$(get_repo_root) || return 1

    log_step "実行権限を設定中..."

    for hook in "${GIT_HOOKS[@]}"; do
        if set_hook_executable "$hook"; then
            log_check_ok "$hook に実行権限を付与しました"
        fi
    done
}

# =============================================================================
# Git フィルター設定
# =============================================================================

# Git フィルターを設定
setup_git_filter() {
    local filter_name="${1:-forbidden}"
    local clean_cmd="${2:-echo 'ERROR: このファイルはGitに追加できません' >&2; exit 1}"
    local smudge_cmd="${3:-cat}"

    log_step "Git フィルターを設定中: $filter_name"

    git config "filter.${filter_name}.clean" "$clean_cmd"
    git config "filter.${filter_name}.smudge" "$smudge_cmd"

    log_check_ok "filter.${filter_name} を設定しました"
}

# Git フィルターが設定されているか確認
check_git_filter() {
    local filter_name="${1:-forbidden}"

    if git config --get "filter.${filter_name}.clean" >/dev/null 2>&1; then
        log_check_ok "filter.${filter_name} は設定済み"
        return 0
    else
        log_check_warn "filter.${filter_name} は未設定"
        return 1
    fi
}

# =============================================================================
# .gitignore 検証
# =============================================================================

# .gitignore に必要なパターンが含まれているかチェック
verify_gitignore() {
    local repo_root
    repo_root=$(get_repo_root) || return 1
    local gitignore="${repo_root}/.gitignore"

    check_file_exists "$gitignore" || return 1

    log_step ".gitignore を検証中..."

    local required_patterns=(
        "^/env/"
        "^/secrets/"
    )

    local all_ok=0

    for pattern in "${required_patterns[@]}"; do
        if grep -q "$pattern" "$gitignore"; then
            log_check_ok "'$pattern' は含まれています"
        else
            log_check_fail "'$pattern' が含まれていません"
            all_ok=1
        fi
    done

    return $all_ok
}

# =============================================================================
# 機密ファイル検出
# =============================================================================

# Git 追跡対象の機密ファイルを検出
detect_tracked_secrets() {
    local repo_root
    repo_root=$(get_repo_root) || return 1

    log_step "Git 追跡対象の機密ファイルをチェック中..."

    local forbidden_files
    forbidden_files=$(git ls-tree -r HEAD --name-only 2>/dev/null | \
        grep -E '^(env/\.env\.|secrets/\.env\..*\.secrets$|secrets/gcp-sa.*\.json$|.*\.pem$|.*\.key$)' | \
        grep -v -E '\.(example|template)$' || true)

    if [[ -n "$forbidden_files" ]]; then
        log_error "機密ファイルが検出されました:"
        echo "$forbidden_files" | while read -r file; do
            log_check_fail "$file"
        done
        return 1
    else
        log_check_ok "機密ファイルは検出されませんでした"
        return 0
    fi
}

# ステージング済みの機密ファイルを検出
detect_staged_secrets() {
    local repo_root
    repo_root=$(get_repo_root) || return 1

    log_step "ステージング済みの機密ファイルをチェック中..."

    local staged_files
    staged_files=$(git diff --cached --name-only 2>/dev/null | \
        grep -E '^(env/\.env\.|secrets/)' | \
        grep -v -E '\.(example|template)$' || true)

    if [[ -n "$staged_files" ]]; then
        log_warn "機密ファイルがステージングされています:"
        echo "$staged_files" | while read -r file; do
            log_check_warn "$file"
        done
        return 1
    else
        log_check_ok "機密ファイルはステージングされていません"
        return 0
    fi
}

# =============================================================================
# Git 履歴検査
# =============================================================================

# Git 履歴内の機密ファイルを検出
detect_secrets_in_history() {
    local repo_root
    repo_root=$(get_repo_root) || return 1

    log_step "Git 履歴内の機密ファイルをチェック中..."

    local patterns=(
        'env/.env.*'
        'secrets/*.secrets'
    )

    local found=0

    for pattern in "${patterns[@]}"; do
        local count
        count=$(git log --all --oneline --full-history -- "$pattern" 2>/dev/null | \
            grep -v -E '\.(example|template)' | wc -l || true)

        if [[ $count -gt 0 ]]; then
            log_check_fail "$pattern: $count コミットで検出"
            found=1
        else
            log_check_ok "$pattern: 検出されず"
        fi
    done

    return $found
}

# Git 履歴内のパスワードパターンを検出
detect_passwords_in_history() {
    local repo_root
    repo_root=$(get_repo_root) || return 1

    log_step "Git 履歴内のパスワードパターンをチェック中..."

    # POSTGRES_PASSWORD の実際の値を検索（変数定義は除外）
    if git log --all -S "POSTGRES_PASSWORD" --pretty=format:"%H" 2>/dev/null | \
       xargs -I {} git show {} 2>/dev/null | \
       grep -q 'POSTGRES_PASSWORD\s*=\s*['\''"][^$][^'\''"]\+['\''"]' 2>/dev/null; then
        log_check_fail "パスワードが検出されました"
        return 1
    else
        log_check_ok "パスワードは検出されませんでした"
        return 0
    fi
}

# =============================================================================
# Git 履歴クリーンアップ
# =============================================================================

# git-filter-repo の存在確認
check_git_filter_repo() {
    if command -v git-filter-repo &> /dev/null; then
        log_check_ok "git-filter-repo はインストール済み"
        return 0
    else
        log_check_fail "git-filter-repo がインストールされていません"
        log_info "インストール方法:"
        log_info "  Ubuntu/Debian: sudo apt-get install git-filter-repo"
        log_info "  macOS: brew install git-filter-repo"
        log_info "  pip: pip3 install git-filter-repo"
        return 1
    fi
}

# リモートをバックアップ用に変更
backup_remote() {
    local remote="${1:-origin}"
    local backup_name="${2:-origin-backup}"

    log_step "リモート '$remote' を '$backup_name' にリネーム中..."

    if git remote rename "$remote" "$backup_name" 2>/dev/null; then
        log_check_ok "リモートを '$backup_name' にリネームしました"
        return 0
    else
        log_warn "リモートのリネームに失敗しました（既に存在する可能性）"
        return 1
    fi
}

# リモートを復元
restore_remote() {
    local backup_name="${1:-origin-backup}"
    local remote="${2:-origin}"

    log_step "リモート '$backup_name' を '$remote' に復元中..."

    if git remote rename "$backup_name" "$remote" 2>/dev/null; then
        log_check_ok "リモートを '$remote' に復元しました"
        return 0
    else
        log_warn "リモートの復元に失敗しました"
        return 1
    fi
}

# =============================================================================
# セキュリティテスト
# =============================================================================

# 機密ファイル追加テスト
test_secret_file_block() {
    local repo_root
    repo_root=$(get_repo_root) || return 1
    local test_file="env/.env.test_temp_$$"

    log_step "機密ファイル追加ブロックのテスト中..."

    # テストファイルを作成
    echo "test" > "$test_file"

    # 追加を試みる
    if git add -f "$test_file" 2>&1 | grep -q "ERROR"; then
        log_check_ok "機密ファイルの追加が正常にブロックされました"
        rm -f "$test_file"
        git reset HEAD "$test_file" 2>/dev/null || true
        return 0
    else
        log_check_fail "機密ファイルの追加がブロックされませんでした"
        rm -f "$test_file"
        git reset HEAD "$test_file" 2>/dev/null || true
        return 1
    fi
}

# =============================================================================
# Git サイズ確認
# =============================================================================

# .git ディレクトリのサイズを取得
get_git_size() {
    local repo_root
    repo_root=$(get_repo_root) || return 1
    du -sh "${repo_root}/.git" 2>/dev/null | cut -f1
}

# Git サイズを表示
show_git_size() {
    local size
    size=$(get_git_size)
    log_info "Git リポジトリサイズ: $size"
}

# =============================================================================
# 初期化
# =============================================================================
log_debug "Git ライブラリの初期化が完了しました"
