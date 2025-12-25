#!/bin/bash
# =============================================================================
# Pre-commit Security Patterns - DSN Detection Tests
# =============================================================================
# DSN（データベース接続文字列）検出のテストケース

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
LIB_DIR="${REPO_ROOT}/scripts/git/lib"

# ライブラリ読み込み
source "${LIB_DIR}/security_patterns.sh"
source "${LIB_DIR}/output_utils.sh"

# テスト結果カウンター
PASSED=0
FAILED=0

# =============================================================================
# テスト用ヘルパー関数
# =============================================================================
test_should_detect() {
    local test_name="$1"
    local test_input="$2"

    local result
    result=$(contains_sensitive_content "$test_input" 2>&1)
    local exit_code=$?

    if [ $exit_code -eq 0 ] && [ -n "$result" ]; then
        echo "✅ PASS: $test_name"
        ((PASSED++))
        return 0
    else
        echo "❌ FAIL: $test_name"
        echo "   Expected: Should detect"
        echo "   Input: $test_input"
        echo "   Exit code: $exit_code"
        echo "   Result: '$result'"
        ((FAILED++))
        return 1
    fi
}

test_should_not_detect() {
    local test_name="$1"
    local test_input="$2"

    local result
    result=$(contains_sensitive_content "$test_input" 2>&1)
    local exit_code=$?

    if [ $exit_code -eq 1 ] || [ -z "$result" ]; then
        echo "✅ PASS: $test_name"
        ((PASSED++))
        return 0
    else
        echo "❌ FAIL: $test_name"
        echo "   Expected: Should NOT detect"
        echo "   Input: $test_input"
        echo "   Exit code: $exit_code"
        echo "   Result: '$result'"
        ((FAILED++))
        return 1
    fi
}

# =============================================================================
# PostgreSQL DSN テスト
# =============================================================================
echo "🧪 Testing PostgreSQL DSN detection..."
echo ""

test_should_detect \
    "PostgreSQL DSN with 8+ char password" \
    "+  DB_DSN: postgresql://user:password123@localhost/db"

test_should_detect \
    "Postgres DSN with long password" \
    "+DATABASE_URL=postgres://myuser:secretpass@db.example.com:5432/production"

test_should_not_detect \
    "PostgreSQL DSN with placeholder" \
    "+  DB_DSN: postgresql://user:\${DB_PASSWORD}@localhost/db"

test_should_not_detect \
    "PostgreSQL DSN with angle bracket placeholder" \
    "+DATABASE_URL: postgresql://user:<password>@localhost/db"

test_should_not_detect \
    "PostgreSQL DSN with short password (7 chars)" \
    "+  DB_DSN: postgresql://user:pass123@localhost/db"

test_should_not_detect \
    "PostgreSQL DSN in documentation" \
    "+Example: \`postgresql://user:example_pass@host/db\`"

echo ""

# =============================================================================
# MySQL DSN テスト
# =============================================================================
echo "🧪 Testing MySQL DSN detection..."
echo ""

test_should_detect \
    "MySQL DSN with 8+ char password" \
    "+  DATABASE_URL: mysql://root:mysqlpassword@localhost:3306/mydb"

test_should_detect \
    "MySQL DSN in docker-compose" \
    "+    DATABASE_URL=mysql://app_user:app_pass_2024@mysql-server/app_db"

test_should_not_detect \
    "MySQL DSN with variable" \
    "+  DB_DSN: mysql://root:\${MYSQL_PASSWORD}@mysql/db"

test_should_not_detect \
    "MySQL DSN with asterisks" \
    "+  DATABASE_URL: mysql://root:********@localhost/db"

echo ""

# =============================================================================
# Redis DSN テスト
# =============================================================================
echo "🧪 Testing Redis DSN detection..."
echo ""

test_should_detect \
    "Redis DSN with 8+ char password" \
    "+  REDIS_URL: redis://:mypassword123@localhost:6379"

test_should_detect \
    "Redis DSN with long password" \
    "+REDIS_URL=redis://:secretkey123@redis.example.com:6379/0"

test_should_not_detect \
    "Redis DSN with placeholder" \
    "+  REDIS_URL: redis://:\${REDIS_PASSWORD}@localhost:6379"

test_should_not_detect \
    "Redis DSN with short password" \
    "+  REDIS_URL: redis://:pass@localhost:6379"

echo ""

# =============================================================================
# docker-compose 環境変数テスト
# =============================================================================
echo "🧪 Testing docker-compose environment variables..."
echo ""

test_should_detect \
    "DB_DSN in docker-compose.yml" \
    "+    DB_DSN: postgresql://user:password@localhost/db"

test_should_detect \
    "DATABASE_URL with quotes" \
    '+    DATABASE_URL="mysql://root:pass12345678@mysql/db"'

test_should_not_detect \
    "DB_DSN with your_ prefix (placeholder)" \
    "+    DB_DSN: postgresql://user:your_password@localhost/db"

test_should_not_detect \
    "DATABASE_URL with example (placeholder)" \
    "+    DATABASE_URL: mysql://user:example_pass@localhost/db"

echo ""

# =============================================================================
# 複雑なケース
# =============================================================================
echo "🧪 Testing complex cases..."
echo ""

test_should_not_detect \
    "Comment line with DSN" \
    "+# DB_DSN: postgresql://user:password123@localhost/db"

test_should_not_detect \
    "Markdown code block" \
    '+```yaml
+DB_DSN: postgresql://user:password123@localhost/db
+```'

test_should_not_detect \
    "Documentation example" \
    "+Example: DB_DSN: postgresql://user:example_password@localhost/db"

echo ""

# =============================================================================
# テスト結果サマリー
# =============================================================================
echo "========================================"
echo "Test Summary"
echo "========================================"
echo "Total: $((PASSED + FAILED))"
echo "✅ Passed: $PASSED"
echo "❌ Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "🎉 All tests passed!"
    exit 0
else
    echo "❌ Some tests failed"
    exit 1
fi
