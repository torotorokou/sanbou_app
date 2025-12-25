#!/usr/bin/env bash
# Detect hardcoded passwords in docs (Markdown/YAML)
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
TARGET_DIR="$ROOT_DIR/docs"

# パスワードパターン: password= or password: 等（$や<>で囲まれないもの）
# ただし、例示用コード（def __init__など）やgetenvは除外
PATTERN='(password|passwd|pwd)[:=]\s*[^$<>{}\s]'

# 検索実行
if git -C "$ROOT_DIR" grep -n -I -E "$PATTERN" -- "$TARGET_DIR" -- '*.md' '*.yml' '*.yaml' 2>/dev/null | \
   grep -v -E '(__SET_IN_|<[A-Z_]+>|例|example|\[マスク|\*\*\*|def __init__|\.getenv\(|password=password|"p@ss)'; then
  echo "Found hardcoded password in docs. Use placeholders like <PASSWORD> or __SET_IN_SECRETS__." >&2
  exit 1
fi

exit 0
