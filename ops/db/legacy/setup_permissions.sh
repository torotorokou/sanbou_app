#!/bin/bash
# Database permissions setup script
# Run this script to grant necessary permissions for core_api to access ref and mart schemas

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SQL_FILE="${SCRIPT_DIR}/grant_schema_permissions.sql"

echo "🔐 Granting database schema permissions..."

docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -f /scripts/db/grant_schema_permissions.sql

echo "✅ Database permissions granted successfully"
echo ""
echo "💡 If core_api is already running, restart it to apply new permissions:"
echo "   docker compose -f docker/docker-compose.dev.yml -p local_dev restart core_api"
