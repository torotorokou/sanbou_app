#!/bin/bash
# =============================================================================
# Core API Acceptance Test Script
# =============================================================================
# This script validates that the core_api meets all acceptance criteria.
#
# Prerequisites:
# - core_api and forecast_worker are running
# - Database is initialized with migrations
#
# Usage:
#   ./test_acceptance.sh
# =============================================================================

set -e

BASE_URL="${CORE_API_URL:-http://localhost:8003}"
API_URL="${BASE_URL}/api"

echo "================================"
echo "Core API Acceptance Tests"
echo "================================"
echo "API URL: $API_URL"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
}

fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    exit 1
}

# Test 1: Health check
echo "Test 1: Health check"
response=$(curl -s -w "%{http_code}" -o /tmp/health.json "$API_URL/healthz")
if [ "$response" = "200" ]; then
    pass "Health check returns 200"
else
    fail "Health check failed with status $response"
fi

# Test 2: Create forecast job
echo ""
echo "Test 2: Create forecast job"
response=$(curl -s -X POST "$API_URL/forecast/jobs" \
    -H "Content-Type: application/json" \
    -d '{"target_from": "2025-01-01", "target_to": "2025-01-31"}')
job_id=$(echo "$response" | jq -r '.id')
status=$(echo "$response" | jq -r '.status')

if [ "$status" = "queued" ]; then
    pass "Job created with id=$job_id, status=queued"
else
    fail "Job creation failed: $response"
fi

# Test 3: Check job status
echo ""
echo "Test 3: Check job status"
response=$(curl -s "$API_URL/forecast/jobs/$job_id")
job_status=$(echo "$response" | jq -r '.status')

if [ -n "$job_status" ]; then
    pass "Job status retrieved: $job_status"
else
    fail "Failed to retrieve job status"
fi

# Test 4: Wait for worker to complete job
echo ""
echo "Test 4: Wait for worker to complete job (max 30s)"
for i in {1..10}; do
    sleep 3
    response=$(curl -s "$API_URL/forecast/jobs/$job_id")
    job_status=$(echo "$response" | jq -r '.status')
    echo "  Attempt $i/10: Job status = $job_status"
    
    if [ "$job_status" = "done" ]; then
        pass "Job completed successfully"
        break
    elif [ "$job_status" = "failed" ]; then
        error_msg=$(echo "$response" | jq -r '.error_message')
        fail "Job failed with error: $error_msg"
    fi
    
    if [ $i -eq 10 ]; then
        fail "Job did not complete within 30 seconds"
    fi
done

# Test 5: Get predictions
echo ""
echo "Test 5: Get predictions"
response=$(curl -s "$API_URL/forecast/predictions?from=2025-01-01&to=2025-01-31")
count=$(echo "$response" | jq 'length')

if [ "$count" -gt 0 ]; then
    pass "Retrieved $count predictions"
else
    fail "No predictions found"
fi

# Test 6: Verify UPSERT idempotency (re-run same job)
echo ""
echo "Test 6: Verify UPSERT idempotency"
response=$(curl -s -X POST "$API_URL/forecast/jobs" \
    -H "Content-Type: application/json" \
    -d '{"target_from": "2025-01-01", "target_to": "2025-01-31"}')
job_id2=$(echo "$response" | jq -r '.id')

# Wait for completion
for i in {1..10}; do
    sleep 3
    response=$(curl -s "$API_URL/forecast/jobs/$job_id2")
    job_status=$(echo "$response" | jq -r '.status')
    if [ "$job_status" = "done" ] || [ "$job_status" = "failed" ]; then
        break
    fi
done

# Check if predictions count is the same (no duplicates)
response2=$(curl -s "$API_URL/forecast/predictions?from=2025-01-01&to=2025-01-31")
count2=$(echo "$response2" | jq 'length')

if [ "$count" -eq "$count2" ]; then
    pass "UPSERT is idempotent (no duplicate predictions)"
else
    fail "UPSERT failed: prediction count changed from $count to $count2"
fi

# Test 7: Create reservation
echo ""
echo "Test 7: Create reservation"
response=$(curl -s -X POST "$API_URL/ingest/reserve" \
    -H "Content-Type: application/json" \
    -d '{"date": "2025-01-15", "trucks": 5}')
reservation_date=$(echo "$response" | jq -r '.date')

if [ "$reservation_date" = "2025-01-15" ]; then
    pass "Reservation created for date $reservation_date"
else
    fail "Reservation creation failed: $response"
fi

# Test 8: External API proxy (RAG)
echo ""
echo "Test 8: External API proxy (RAG)"
response=$(curl -s -w "%{http_code}" -o /tmp/rag.json -X POST "$API_URL/external/rag/ask" \
    -H "Content-Type: application/json" \
    -d '{"query": "test query"}')

if [ "$response" = "200" ] || [ "$response" = "504" ]; then
    pass "RAG proxy endpoint accessible (status $response)"
else
    fail "RAG proxy failed with status $response"
fi

# Test 9: KPI overview
echo ""
echo "Test 9: KPI overview"
response=$(curl -s "$API_URL/kpi/overview")
total_jobs=$(echo "$response" | jq -r '.total_jobs')

if [ "$total_jobs" -ge 2 ]; then
    pass "KPI overview shows $total_jobs total jobs"
else
    fail "KPI overview failed or shows incorrect data"
fi

echo ""
echo "================================"
echo "All Acceptance Tests Passed! ✓"
echo "================================"
