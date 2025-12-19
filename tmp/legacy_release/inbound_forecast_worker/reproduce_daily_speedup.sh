#!/bin/bash
# daily_speedup_retry_20251106_134600 の再現スクリプト
#
# 前提:
# - data/input/20240501-20250422.csv (明細データ) が存在すること
# - data/input/yoyaku_data.csv (予約データ) が存在すること
#
# 設定 (run_metadata.json より復元):
# - top_n: 6
# - min_stage1_days: 120
# - share_oof_models: 2
# - max_history_days: 290
# - calibration_window_days: 28
# - zero_cap_quantile: 0.15
# - n_splits: 3 (推定)
# - n_jobs: -1 (並列実行)

OUT_DIR="data/output/reproduce_daily_speedup"
mkdir -p "$OUT_DIR"

echo "Starting reproduction of daily_speedup_retry_20251106_134600..."
echo "Output directory: $OUT_DIR"

python3 scripts/train_daily_model.py \
  --raw-csv data/input/20240501-20250422.csv \
  --reserve-csv data/input/yoyaku_data.csv \
  --raw-date-col 伝票日付 \
  --raw-item-col 品名 \
  --raw-weight-col 正味重量 \
  --reserve-date-col 予約日 \
  --reserve-count-col 台数 \
  --reserve-fixed-col 固定客 \
  --out-dir "$OUT_DIR" \
  --save-bundle "$OUT_DIR/model_bundle.joblib" \
  --n-splits 3 \
  --n-jobs -1 \
  --no-plots \
  --top-n 6 \
  --min-stage1-days 120 \
  --share-oof-models 2 \
  --max-history-days 290 \
  --calibration-window-days 28 \
  --zero-cap-quantile 0.15

echo "Done. Results saved to $OUT_DIR"
