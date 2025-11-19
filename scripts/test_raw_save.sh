#!/bin/bash
# raw層への保存をテストするスクリプト

set -e

echo "========================================="
echo "raw層保存テスト開始"
echo "========================================="

# テストCSVファイルのパス
RECEIVE_CSV="/home/koujiro/work_env/22.Work_React/sanbou_app/test_receive_mini.csv"

# core_api のURL
API_URL="http://localhost:8003/database/upload/shogun_csv_flash"

echo ""
echo "1. テーブルをクリア"
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db psql -U myuser -d sanbou_dev -c "
TRUNCATE TABLE raw.receive_shogun_flash;
TRUNCATE TABLE stg.receive_shogun_flash;
"

echo ""
echo "2. CSVをアップロード"
curl -X POST "$API_URL" \
  -F "receive=@$RECEIVE_CSV" \
  -H "Content-Type: multipart/form-data" \
  | jq '.'

echo ""
echo "3. raw層のデータ件数確認"
RAW_COUNT=$(docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db psql -U myuser -d sanbou_dev -t -c "SELECT COUNT(*) FROM raw.receive_shogun_flash;")
echo "raw.receive_shogun_flash: $RAW_COUNT 件"

echo ""
echo "4. stg層のデータ件数確認"
STG_COUNT=$(docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db psql -U myuser -d sanbou_dev -t -c "SELECT COUNT(*) FROM stg.receive_shogun_flash;")
echo "stg.receive_shogun_flash: $STG_COUNT 件"

echo ""
echo "5. raw層のサンプルデータ確認（最初の1件）"
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db psql -U myuser -d sanbou_dev -c "
SELECT slip_date, vendor_cd, vendor_name, item_name, net_weight
FROM raw.receive_shogun_flash
LIMIT 1;
"

echo ""
echo "========================================="
echo "テスト完了"
echo "========================================="

if [ "$RAW_COUNT" -gt 0 ]; then
  echo "✅ raw層への保存: 成功"
else
  echo "❌ raw層への保存: 失敗"
  exit 1
fi

if [ "$STG_COUNT" -gt 0 ]; then
  echo "✅ stg層への保存: 成功"
else
  echo "❌ stg層への保存: 失敗"
  exit 1
fi
