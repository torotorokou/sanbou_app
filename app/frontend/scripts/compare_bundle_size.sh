#!/bin/bash
# バンドルサイズ比較スクリプト
# 使用方法: ./scripts/compare_bundle_size.sh

echo "========================================="
echo "  Bundle Size Comparison Report"
echo "========================================="
echo ""

DIST_DIR="./dist/assets"

if [ ! -d "$DIST_DIR" ]; then
  echo "❌ Error: dist/assets directory not found."
  echo "Run 'npm run build' first."
  exit 1
fi

echo "📊 Top 10 Largest JS Files:"
echo ""

find "$DIST_DIR" -name "*.js" -type f -exec ls -lh {} \; | \
  awk '{print $5, $9}' | \
  sort -hr | \
  head -10 | \
  nl

echo ""
echo "📈 Total JS Size:"
find "$DIST_DIR" -name "*.js" -type f -exec ls -l {} \; | \
  awk '{sum += $5} END {printf "%.2f MB\n", sum/1024/1024}'

echo ""
echo "📦 Vendor Chunks:"
find "$DIST_DIR" -name "vendor-*.js" -type f -exec ls -lh {} \; | \
  awk '{print $5, $9}' | \
  sed 's|.*/||' | \
  column -t

echo ""
echo "💡 Tips:"
echo "  - Run 'npm run build:analyze' to see detailed report"
echo "  - Open dist/stats.html for interactive visualization"
echo "  - Check docs/BUNDLE_OPTIMIZATION.md for optimization guide"
echo ""
echo "========================================="
