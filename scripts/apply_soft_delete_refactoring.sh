#!/bin/bash
# ============================================================================
# 論理削除（Soft Delete）対応マイグレーション実行スクリプト
# ============================================================================
# 
# このスクリプトは以下を実行します:
#   1. Alembic マイグレーションの適用
#   2. マテリアライズドビューのリフレッシュ
#   3. 統計情報の更新
#   4. リグレッションテストの実行
#
# 使い方:
#   ./scripts/apply_soft_delete_refactoring.sh
#
# ============================================================================

set -euo pipefail

# 色付きログ出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Docker Compose コマンドの設定
DC="docker compose -f docker/docker-compose.dev.yml -p local_dev"
DB_EXEC="$DC exec -T db psql -U myuser -d sanbou_dev"
API_EXEC="$DC exec core_api"

# ============================================================================
# Step 1: Alembic マイグレーションの適用
# ============================================================================
log_info "=========================================="
log_info "Step 1: Applying Alembic migrations"
log_info "=========================================="

log_info "Current revision:"
$API_EXEC alembic -c /backend/migrations/alembic.ini current

log_info ""
log_info "Upgrading to head..."
$API_EXEC alembic -c /backend/migrations/alembic.ini upgrade head

log_success "Alembic migrations applied successfully"
log_info ""

# ============================================================================
# Step 2: マテリアライズドビューのリフレッシュ
# ============================================================================
log_info "=========================================="
log_info "Step 2: Refreshing materialized views"
log_info "=========================================="

log_warning "This may take several minutes depending on data volume..."

# 各マテリアライズドビューをリフレッシュ
MVS=(
    "mart.mv_target_card_per_day"
    "mart.mv_inb5y_week_profile_min"
    "mart.mv_inb_avg5y_day_biz"
    "mart.mv_inb_avg5y_weeksum_biz"
    "mart.mv_inb_avg5y_day_scope"
)

for mv in "${MVS[@]}"; do
    log_info "Refreshing $mv..."
    $DB_EXEC -c "REFRESH MATERIALIZED VIEW CONCURRENTLY $mv;" || {
        log_error "Failed to refresh $mv"
        exit 1
    }
    log_success "✓ $mv refreshed"
done

log_success "All materialized views refreshed successfully"
log_info ""

# ============================================================================
# Step 3: 統計情報の更新
# ============================================================================
log_info "=========================================="
log_info "Step 3: Updating table statistics"
log_info "=========================================="

TABLES=(
    "stg.shogun_flash_receive"
    "stg.shogun_final_receive"
    "stg.shogun_flash_yard"
    "stg.shogun_final_yard"
    "stg.shogun_flash_shipment"
    "stg.shogun_final_shipment"
)

for table in "${TABLES[@]}"; do
    log_info "Analyzing $table..."
    $DB_EXEC -c "ANALYZE $table;" || {
        log_warning "Failed to analyze $table (non-critical)"
    }
    log_success "✓ $table analyzed"
done

log_success "Table statistics updated successfully"
log_info ""

# ============================================================================
# Step 4: リグレッションテストの実行
# ============================================================================
log_info "=========================================="
log_info "Step 4: Running regression tests"
log_info "=========================================="

TEST_SQL="scripts/sql/test_is_deleted_regression.sql"

if [ ! -f "$TEST_SQL" ]; then
    log_error "Test SQL file not found: $TEST_SQL"
    exit 1
fi

log_info "Executing regression tests..."
$DB_EXEC < "$TEST_SQL" > /tmp/soft_delete_test_results.txt 2>&1 || {
    log_error "Regression tests failed. Check /tmp/soft_delete_test_results.txt for details."
    exit 1
}

log_success "Regression tests completed successfully"
log_info "Test results saved to: /tmp/soft_delete_test_results.txt"
log_info ""

# ============================================================================
# Step 5: 結果サマリー
# ============================================================================
log_info "=========================================="
log_info "Migration Summary"
log_info "=========================================="

log_info "Applied migrations:"
$API_EXEC alembic -c /backend/migrations/alembic.ini current

log_info ""
log_info "Active views created:"
log_info "  - stg.active_shogun_flash_receive"
log_info "  - stg.active_shogun_final_receive"
log_info "  - stg.active_shogun_flash_yard"
log_info "  - stg.active_shogun_final_yard"
log_info "  - stg.active_shogun_flash_shipment"
log_info "  - stg.active_shogun_final_shipment"

log_info ""
log_info "Updated views:"
log_info "  - mart.v_receive_daily"
log_info "  - mart.v_shogun_flash_receive_daily"
log_info "  - mart.v_shogun_final_receive_daily"

log_info ""
log_info "Partial indexes created:"
log_info "  - idx_shogun_flash_receive_active"
log_info "  - idx_shogun_final_receive_active"
log_info "  - idx_shogun_flash_yard_active"
log_info "  - idx_shogun_final_yard_active"
log_info "  - idx_shogun_flash_shipment_active"
log_info "  - idx_shogun_final_shipment_active"

log_info ""
log_success "=========================================="
log_success "Migration completed successfully! 🎉"
log_success "=========================================="

log_info ""
log_info "Next steps:"
log_info "  1. Review test results: cat /tmp/soft_delete_test_results.txt"
log_info "  2. Verify API responses in development environment"
log_info "  3. Deploy to staging environment for further testing"
log_info "  4. Monitor query performance with EXPLAIN ANALYZE"

log_info ""
log_info "For detailed documentation, see:"
log_info "  docs/SOFT_DELETE_REFACTORING_20251120.md"
