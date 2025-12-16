#!/bin/bash
set -e

# 作業ディレクトリをこのスクリプトのあるディレクトリの親(submission root)に移動
cd "$(dirname "$0")"

echo "=== 1. 月次特徴量の作成 (Daily -> Monthly) ==="
mkdir -p data/output
python3 scripts/monthly_landing_gamma_poisson/build_monthly_from_daily.py \
  --daily-csv data/input/01_daily_clean.csv \
  --out-csv data/output/monthly_features.csv

echo "=== 2. モデル学習と保存 (Training & Saving) ==="
mkdir -p models

# 14日版モデル
echo "Training 14-day model..."
python3 scripts/monthly_landing_gamma_poisson/run_monthly_landing_gamma_poisson.py \
  --monthly-csv data/output/monthly_features.csv \
  --save-model models/monthly_landing_poisson_14d.pkl

# 21日版モデル (A_t1_21 使用)
echo "Training 21-day model..."
python3 scripts/monthly_landing_gamma_poisson/run_monthly_landing_gamma_poisson.py \
  --monthly-csv data/output/monthly_features.csv \
  --use-a21 \
  --save-model models/monthly_landing_poisson_21d.pkl

echo "=== 3. 推論と評価 (Inference & Evaluation) ==="
mkdir -p output

# 14日版推論
python3 scripts/monthly_landing_gamma_poisson/run_monthly_landing_gamma_poisson.py \
  --monthly-csv data/output/monthly_features.csv \
  --load-model models/monthly_landing_poisson_14d.pkl \
  --out-csv output/prediction_14d.csv

# 21日版推論
python3 scripts/monthly_landing_gamma_poisson/run_monthly_landing_gamma_poisson.py \
  --monthly-csv data/output/monthly_features.csv \
  --load-model models/monthly_landing_poisson_21d.pkl \
  --out-csv output/prediction_21d.csv

echo "=== 完了 ==="
echo "出力ファイル:"
echo "  - data/output/monthly_features.csv"
echo "  - models/monthly_landing_poisson_14d.pkl"
echo "  - models/monthly_landing_poisson_21d.pkl"
echo "  - output/prediction_14d.csv"
echo "  - output/prediction_21d.csv"
