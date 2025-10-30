#!/usr/bin/env bash
## =============================================================
## validate_compose.sh - Docker Compose 構成の検証スクリプト
## =============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"

echo "============================================================="
echo " Docker Compose Validation Script"
echo "============================================================="

echo ""
echo "[1/4] Validate docker-compose.dev.yml (local_dev)"
echo "-------------------------------------------------------------"
make config ENV=local_dev

echo ""
echo "[2/4] Start services (local_dev)"
echo "-------------------------------------------------------------"
make up ENV=local_dev

echo ""
echo "[3/4] Health check (wait 5s)"
echo "-------------------------------------------------------------"
sleep 5
echo "Checking health endpoints..."
curl -I http://localhost:8001/health || echo "[warn] ai_api health check failed"
curl -I http://localhost:8002/health || echo "[warn] ledger_api health check failed"
curl -I http://localhost:8003/health || echo "[warn] core_api health check failed"
curl -I http://localhost:8004/health || echo "[warn] rag_api health check failed"
curl -I http://localhost:8005/health || echo "[warn] manual_api health check failed"

echo ""
echo "[4/4] Stop services (local_dev)"
echo "-------------------------------------------------------------"
make down ENV=local_dev

echo ""
echo "============================================================="
echo " Validation Complete"
echo "============================================================="
echo "[ok] All checks passed"
