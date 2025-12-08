#!/bin/bash
# =============================================================================
# .gitignore 整合性チェッカー
# =============================================================================
# .gitignore の設定が適切かどうかを検証し、問題があれば修正提案を行う

set -e

# 共通ライブラリの読み込み
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/security_patterns.sh"
source "${SCRIPT_DIR}/lib/output_utils.sh"

# =============================================================================
# メイン処理
# =============================================================================

main() {
    log_section ".gitignore 整合性チェック"
    
    local repo_root
    repo_root=$(git rev-parse --show-toplevel 2>/dev/null)
    
    if [ -z "$repo_root" ]; then
        log_error "Git リポジトリではありません"
        exit 1
    fi
    
    local gitignore_file="${repo_root}/.gitignore"
    
    if [ ! -f "$gitignore_file" ]; then
        log_error ".gitignore が見つかりません: $gitignore_file"
        exit 1
    fi
    
    log_info ".gitignore: $gitignore_file"
    echo ""
    
    # .gitignore の内容を読み込み
    local gitignore_content
    gitignore_content=$(cat "$gitignore_file")
    
    # =============================================================================
    # チェック 1: 必須パターンの確認
    # =============================================================================
    log_check 1 3 "必須パターンの確認"
    
    if check_gitignore_patterns "$gitignore_content"; then
        log_success "すべての必須パターンが含まれています"
    else
        log_error "必須パターンが不足しています"
    fi
    echo ""
    
    # =============================================================================
    # チェック 2: 実際に追跡されているファイルの確認
    # =============================================================================
    log_check 2 3 "追跡ファイルの確認"
    
    local tracked_forbidden
    tracked_forbidden=$(git ls-files | while IFS= read -r file; do
        if is_forbidden_file "$file"; then
            echo "$file"
        fi
    done)
    
    if [ -n "$tracked_forbidden" ]; then
        log_error "Git 追跡対象に機密ファイルが含まれています"
        echo ""
        echo "$tracked_forbidden" | while IFS= read -r file; do
            log_file "$file"
        done
        echo ""
        log_info "これらのファイルを管理外にする:"
        echo "  ${CYAN}git rm --cached <file>${NC}"
        echo ""
    else
        log_success "機密ファイルは追跡されていません"
    fi
    echo ""
    
    # =============================================================================
    # チェック 3: 管理外にすべきファイルの存在確認
    # =============================================================================
    log_check 3 3 "管理外ファイルの検出"
    
    local untracked_secrets
    untracked_secrets=$(find "$repo_root/env" "$repo_root/secrets" -type f 2>/dev/null | while IFS= read -r file; do
        local relative_path="${file#$repo_root/}"
        
        # テンプレートやREADMEは除外
        if [[ ! "$relative_path" =~ \.(example|template)$ ]] && [[ ! "$relative_path" =~ README\.md$ ]]; then
            # Git 追跡外か確認
            if ! git ls-files --error-unmatch "$file" > /dev/null 2>&1; then
                echo "$relative_path"
            fi
        fi
    done)
    
    if [ -n "$untracked_secrets" ]; then
        log_success "管理外の機密ファイルが存在します（正常）"
        echo ""
        local count
        count=$(echo "$untracked_secrets" | wc -l)
        log_info "$count 件のファイルが適切に管理外になっています"
        
        # 最初の5件のみ表示
        echo "$untracked_secrets" | head -5 | while IFS= read -r file; do
            echo "  • $file"
        done
        
        if [ "$count" -gt 5 ]; then
            echo "  ... (他 $((count - 5)) 件)"
        fi
    else
        log_info "管理外の機密ファイルはありません"
    fi
    echo ""
    
    # =============================================================================
    # 最終結果
    # =============================================================================
    log_section "チェック完了"
    echo ""
}

main "$@"
