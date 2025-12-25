#!/bin/bash
# =============================================================================
# Git フックセットアップスクリプト
# =============================================================================
# チームメンバーがクローン後に実行するスクリプト
# 機密ファイルの誤コミット/プッシュを防止する Git フックをインストール

# 共通ライブラリの読み込み
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/common.sh"
source "${SCRIPT_DIR}/../lib/git_utils.sh"

# =============================================================================
# メイン処理
# =============================================================================

main() {
    show_script_header "Git セキュリティフックのセットアップ" \
        "機密ファイルの誤コミット/プッシュを防止するフックをインストールします"

    # Git リポジトリのルートディレクトリを取得
    local repo_root
    repo_root=$(get_repo_root) || exit 1

    cd "$repo_root" || exit 1

    log_info "セットアップ先: $repo_root"
    echo ""

    # 各フックの存在確認
    check_all_hooks
    echo ""

    # 実行権限を設定
    set_all_hooks_executable
    echo ""

    # Git フィルター設定
    setup_git_filter
    echo ""

    # .gitignore の検証
    verify_gitignore || exit 1
    echo ""

    # テストケース
    if test_secret_file_block; then
        echo ""
    else
        log_warn "フックのテストに失敗しました（手動確認推奨）"
        echo ""
    fi

    # サマリー
    log_section "✅ セットアップが完了しました"

    log_info "インストールされたフック:"
    for hook in "${GIT_HOOKS[@]}"; do
        if check_hook_exists "$hook"; then
            log_check_ok "$hook"
        fi
    done
    echo ""

    log_warn "【重要】以下のファイルは絶対に Git に追加しないでください:"
    echo "  - env/.env.* （.example と .template 以外）"
    echo "  - secrets/*.secrets"
    echo "  - secrets/*.json（GCP 鍵）"
    echo "  - *.pem, *.key（秘密鍵）"
    echo ""
    log_info "これらのファイルを誤って追加しようとすると、フックがエラーを出して防ぎます。"
    echo ""
}

# =============================================================================
# スクリプト実行
# =============================================================================
main "$@"
