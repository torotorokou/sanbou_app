#!/usr/bin/env bash
# Detect hardcoded passwords in docs (Markdown/YAML) - check staged changes only
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# パスワードパターン: password= or password: 等（$や<>で囲まれないもの）
# ただし、例示用コード（def __init__など）やgetenvは除外
PATTERN='(password|passwd|pwd)[:=]\s*[^$<>{}\s]'

# ステージされた追加行のみをチェック（削除行は無視）
# --cached: ステージされた変更を対象
# --diff-filter=AM: 追加・変更のみ（削除は除外）
staged_files=$(git diff --cached --name-only --diff-filter=AM -- 'docs/*.md' 'docs/*.yml' 'docs/*.yaml' '*.md' 2>/dev/null || true)

if [ -z "$staged_files" ]; then
  # ステージされたファイルがない場合はスキップ
  exit 0
fi

# 各ファイルの追加行のみを取得してチェック
for file in $staged_files; do
  added_lines=$(git diff --cached --unified=0 "$file" | sed -n '/^+++/d;/^+/s/^+//p')
  [ -z "$added_lines" ] && continue

  # パターンマッチ + 除外パターンのフィルタ
  if echo "$added_lines" | grep -E "$PATTERN" | \
     grep -v -E '(__SET_IN_|<[A-Z_]+>|<PASSWORD>|例|example|\[マスク|\*\*\*|def __init__|\.getenv\(|password=password|"p@ss)' > /dev/null; then
    echo "❌ Found hardcoded password in staged changes of $file. Use placeholders like <PASSWORD> or __SET_IN_SECRETS__." >&2
    exit 1
  fi
done

exit 0
