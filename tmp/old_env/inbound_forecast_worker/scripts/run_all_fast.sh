#!/usr/bin/env bash
set -euo pipefail

TS=$(date +%Y%m%d_%H%M%S)
BASE="/works/data/submission_release_20251027"
INP="$BASE/data/input"
OUT="$BASE/data/output"
DAILY_OUT="$OUT/daily_fast_${TS}"
WEEKLY_OUT="$OUT/weekly_fast_${TS}"
LOG="$OUT/run_all_fast_${TS}.log"

mkdir -p "$DAILY_OUT" "$WEEKLY_OUT" "$OUT"

echo "[RUN] $(date -Is) start pipeline -> $LOG" | tee -a "$LOG"

echo "[STEP1] Daily train/eval -> $DAILY_OUT" | tee -a "$LOG"
python3 "$BASE/scripts/train_daily_model.py" \
  --raw-csv "/works/data/input/20240501-20250422.csv" \
  --reserve-csv "$INP/yoyaku_data.csv" \
  --out-dir "$DAILY_OUT" \
  --save-bundle "$DAILY_OUT/model_bundle.joblib" \
  --retrain-interval 3 --n-splits 3 \
  --rf-n-estimators 120 --gbr-n-estimators 140 \
  --n-jobs -1 --disable-elastic --no-plots 2>&1 | tee -a "$LOG"

if [[ ! -f "$DAILY_OUT/model_bundle.joblib" || ! -f "$DAILY_OUT/res_walkforward.csv" ]]; then
  echo "[ERROR] Daily artifacts missing. See log: $LOG" | tee -a "$LOG"
  exit 1
fi

echo "[STEP2] Weekly train/eval -> $WEEKLY_OUT" | tee -a "$LOG"
python3 "$BASE/scripts/train_weekly_model.py" \
  --base-bundle "$DAILY_OUT/model_bundle.joblib" \
  --res-walk-csv "$DAILY_OUT/res_walkforward.csv" \
  --reserve-csv "$INP/yoyaku_data.csv" \
  --out-dir "$WEEKLY_OUT" \
  --weeks 8 --method lgbm --fast --skip-stacking 2>&1 | tee -a "$LOG"

if [[ ! -f "$WEEKLY_OUT/weekly_bundle.joblib" ]]; then
  echo "[WARN] Weekly bundle not found. Continue. See log: $LOG" | tee -a "$LOG"
fi

echo "[STEP3] Monthly train/eval (fast)" | tee -a "$LOG"
python3 "$BASE/scripts/morioka/train_monthly_gamma_blend.py" --fast --no-plots 2>&1 | tee -a "$LOG"

echo "[DONE] $(date -Is) pipeline finished" | tee -a "$LOG"
