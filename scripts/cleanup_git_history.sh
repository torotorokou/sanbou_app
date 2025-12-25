#!/bin/bash
# =============================================================================
# Git 履歴から機密ファイルを完全削除するスクリプト
# =============================================================================
# 使用方法:
#   bash scripts/cleanup_git_history.sh
#
# 注意:
# - このスクリプトは Git 履歴を書き換えます
# - 実行前に必ずバックアップを取ってください
# - チーム全員に通知し、再クローンを依頼する必要があります

# 共通ライブラリの読み込み
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"
source "${SCRIPT_DIR}/lib/git_utils.sh"

# =============================================================================
# 削除対象ファイルのリスト
# =============================================================================
declare -a FILES_TO_REMOVE=(
    "env/.env.common"
    "env/.env.local_dev"
    "env/.env.local_stg"
    "env/.env.local_demo"
    "env/.env.vm_stg"
    "env/.env.vm_prod"
    "secrets/.env.local_dev.secrets"
    "secrets/.env.local_demo.secrets"
    "secrets/.env.local_stg.secrets"
    "secrets/.env.vm_stg.secrets"
    "secrets/.env.vm_prod.secrets"
)

# =============================================================================
# メイン処理
# =============================================================================

main() {
    show_script_header "Git 履歴から機密ファイルを削除" \
        "⚠️  この操作は Git 履歴を書き換えます"

    # Git リポジトリのルートを取得
    local repo_root
    repo_root=$(get_repo_root) || exit 1
    cd "$repo_root"

    # 確認
    log_warn "以下を確認してください:"
    echo "1. ✅ バックアップを取得済み"
    echo "2. ✅ チームメンバーに通知済み"
    echo "3. ✅ 作業中のブランチがないことを確認"
    echo "4. ✅ この操作後、全員が再クローンする必要があります"
    echo ""

    confirm_critical "Git 履歴を書き換えます" || {
        log_info "キャンセルしました"
        exit 0
    }
    echo ""

    # Step 1: git-filter-repo の確認
    log_section "Step 1: git-filter-repo の確認"
    check_git_filter_repo || exit 1
    echo ""

    # Step 2: バックアップ作成
    log_section "Step 2: バックアップ作成"
    local backup_file
    backup_file=$(create_tar_backup ".git") || exit 1
    log_success "バックアップ: $backup_file"
    echo ""

    # Step 3: リモートの一時的な変更
    log_section "Step 3: リモートの一時的な変更"
    backup_remote "origin" "origin-backup"
    echo ""

    # Step 4: 削除対象ファイルのリストアップ
    log_section "Step 4: 削除対象ファイルのリストアップ"
    log_info "以下のファイルを履歴から削除します:"
    for file in "${FILES_TO_REMOVE[@]}"; do
        echo "  - $file"
    done
    echo ""

    # Step 5: git-filter-repo による履歴削除
    log_section "Step 5: git-filter-repo による履歴削除"

    # 削除コマンドを構築
    local filter_args=""
    for file in "${FILES_TO_REMOVE[@]}"; do
        filter_args="$filter_args --path $file --invert-paths"
    done

    log_step "実行中..."
    if git filter-repo $filter_args --force; then
        log_success "履歴から削除完了"
    else
        log_error "履歴削除に失敗しました"
        restore_remote "origin-backup" "origin"
        exit 1
    fi
    echo ""

    # Step 6: リモートの復元
    log_section "Step 6: リモートの復元"
    restore_remote "origin-backup" "origin"
    echo ""

    # Step 7: Git のクリーンアップ
    log_section "Step 7: Git のクリーンアップ"
    log_step "Git データベースを最適化中..."
    git reflog expire --expire=now --all
    git gc --prune=now --aggressive
    log_success "Git データベースを最適化しました"
    echo ""

    # Step 8: Git サイズの確認
    log_section "Step 8: Git サイズの確認"
    show_git_size
    echo ""

    # 完了メッセージ
    log_section "✅ 完了しました"

    log_warn "次のステップ:"
    echo ""
    echo "1. リモートに強制プッシュ:"
    log_info "   git push origin --force --all"
    log_info "   git push origin --force --tags"
    echo ""
    echo "2. チームメンバーに通知:"
    echo "   - 既存のローカルリポジトリを削除"
    echo "   - 新規に git clone を実行"
    echo ""
    echo "3. GitHub の branch protection を一時的に無効化する必要がある場合があります"
    echo ""
    log_error "⚠️  注意: まだリモートにプッシュしていません"
    log_error "   変更内容を確認してから、上記のコマンドでプッシュしてください"
    echo ""
}

# =============================================================================
# スクリプト実行
# =============================================================================
main "$@"
