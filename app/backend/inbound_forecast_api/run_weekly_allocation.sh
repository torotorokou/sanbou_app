#!/bin/bash
set -e

# カレントディレクトリをスクリプトのある場所(submission root)に移動
cd "$(dirname "$0")"

echo "============================================================"
echo "週次モデル (Weekly Allocation) 実行スクリプト"
echo "============================================================"

# 前提ファイルの確認
MONTHLY_FORECAST="data/output/gamma_recency_model/blended_future_forecast.csv"
if [ ! -f "$MONTHLY_FORECAST" ]; then
    echo "[ERROR] 月次予測ファイルが見つかりません: $MONTHLY_FORECAST"
    echo "先に run_monthly_gamma_blend.sh を実行してください。"
    exit 1
fi

echo "月次予測を週次に按分中..."
python3 scripts/weekly_allocation/allocate_monthly_to_weekly_from_blend.py \
  --historical-daily-csv data/input/01_daily_clean.csv \
  --monthly-forecast-csv "$MONTHLY_FORECAST" \
  --out data/output/gamma_recency_model/weekly_allocated_forecast.csv \
  --lookback-years 3

echo "------------------------------------------------------------"
echo "完了しました。"
echo "出力ファイル: data/output/gamma_recency_model/weekly_allocated_forecast.csv"
