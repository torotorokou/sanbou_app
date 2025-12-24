#!/bin/bash
# 簡易デバッグスクリプト

cd /home/koujiro/work_env/22.Work_React/sanbou_app
source scripts/git/lib/security_patterns.sh

echo "=== パターン確認 ==="
echo "パターン数: ${#SENSITIVE_CONTENT_PATTERNS[@]}"
for i in "${!SENSITIVE_CONTENT_PATTERNS[@]}"; do
    echo "[$i]: ${SENSITIVE_CONTENT_PATTERNS[$i]}"
done

echo ""
echo "=== テストケース 1 ==="
test_input="+  DB_DSN: postgresql://user:password123@localhost/db"
echo "Input: $test_input"

# 各パターンを個別にテスト
for pattern in "${SENSITIVE_CONTENT_PATTERNS[@]}"; do
    if echo "$test_input" | grep -qE "$pattern"; then
        echo "✓ Match: $pattern"
    fi
done

echo ""
echo "=== contains_sensitive_content 関数テスト ==="
result=$(contains_sensitive_content "$test_input")
exit_code=$?
echo "Exit code: $exit_code"
echo "Result: '$result'"

echo ""
echo "=== 除外パターン確認 ==="
for exclusion in "${CONTENT_EXCLUSION_PATTERNS[@]}"; do
    if echo "$test_input" | grep -qE "$exclusion"; then
        echo "⚠ 除外パターンにマッチ: $exclusion"
    fi
done
