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
# =============================================================================

set -e

# 色付き出力
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Git 履歴から機密ファイルを削除します${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 確認
echo -e "${YELLOW}⚠️  この操作は Git 履歴を書き換えます。以下を確認してください:${NC}"
echo ""
echo "1. ✅ バックアップを取得済み"
echo "2. ✅ チームメンバーに通知済み"
echo "3. ✅ 作業中のブランチがないことを確認"
echo "4. ✅ この操作後、全員が再クローンする必要があります"
echo ""
echo -e "${RED}本当に実行しますか? (yes/NO)${NC}"
read -r response

if [[ ! "$response" == "yes" ]]; then
    echo "キャンセルしました"
    exit 0
fi

echo ""
echo -e "${GREEN}Step 1: git-filter-repo のインストール確認${NC}"

if ! command -v git-filter-repo &> /dev/null; then
    echo "git-filter-repo がインストールされていません"
    echo ""
    echo "インストール方法:"
    echo "  Ubuntu/Debian: sudo apt-get install git-filter-repo"
    echo "  macOS:         brew install git-filter-repo"
    echo "  pip:           pip3 install git-filter-repo"
    echo ""
    exit 1
fi

echo "✓ git-filter-repo が利用可能です"
echo ""

echo -e "${GREEN}Step 2: リモートの一時的な削除${NC}"
git remote rename origin origin-backup 2>/dev/null || true
echo "✓ リモート origin を origin-backup に変更"
echo ""

echo -e "${GREEN}Step 3: 削除対象ファイルのリストアップ${NC}"

# 削除するファイルパターン
FILES_TO_REMOVE=(
    "env/.env.common"
    "env/.env.local_dev"
    "env/.env.local_stg"
    "env/.env.vm_stg"
    "env/.env.vm_prod"
    "env/.env.local_prod"
    "secrets/.env.local_dev.secrets"
    "secrets/.env.local_stg.secrets"
    "secrets/.env.vm_stg.secrets"
    "secrets/.env.vm_prod.secrets"
)

echo "以下のファイルを履歴から削除します:"
for file in "${FILES_TO_REMOVE[@]}"; do
    echo "  - $file"
done
echo ""

echo -e "${GREEN}Step 4: git-filter-repo による履歴削除${NC}"

# 削除コマンドを構築
FILTER_ARGS=""
for file in "${FILES_TO_REMOVE[@]}"; do
    FILTER_ARGS="$FILTER_ARGS --path $file --invert-paths"
done

# 実行
echo "実行中..."
git filter-repo $FILTER_ARGS --force

echo "✓ 履歴から削除完了"
echo ""

echo -e "${GREEN}Step 5: リモートの復元${NC}"
git remote rename origin-backup origin 2>/dev/null || true
echo "✓ リモート origin を復元"
echo ""

echo -e "${GREEN}Step 6: Git のクリーンアップ${NC}"
git reflog expire --expire=now --all
git gc --prune=now --aggressive
echo "✓ Git データベースを最適化"
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ 完了しました${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}次のステップ:${NC}"
echo ""
echo "1. リモートに強制プッシュ:"
echo "   ${BLUE}git push origin --force --all${NC}"
echo "   ${BLUE}git push origin --force --tags${NC}"
echo ""
echo "2. チームメンバーに通知:"
echo "   - 既存のローカルリポジトリを削除"
echo "   - 新規に git clone を実行"
echo ""
echo "3. GitHub の branch protection を一時的に無効化する必要がある場合があります"
echo ""
echo -e "${RED}⚠️  注意: まだリモートにプッシュしていません${NC}"
echo -e "${RED}   変更内容を確認してから、上記のコマンドでプッシュしてください${NC}"
