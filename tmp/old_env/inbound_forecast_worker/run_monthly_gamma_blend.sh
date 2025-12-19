#!/bin/bash
set -e

# カレントディレクトリをスクリプトのある場所(submission root)に移動
cd "$(dirname "$0")"

echo "============================================================"
echo "月次モデル (Gamma Recency + Blend) 実行スクリプト"
echo "============================================================"

echo "[1/2] Gamma Recency モデルの実行..."
python3 scripts/gamma_recency_model/gamma_recency_model.py

echo "[2/2] ブレンドモデル (Ridge/LGBM) の実行..."
python3 scripts/gamma_recency_model/blend_lgbm.py

echo "------------------------------------------------------------"
echo "完了しました。"
echo "出力先: data/output/gamma_recency_model/"
echo "  - blended_prediction_results.csv (評価用)"
echo "  - blended_future_forecast.csv (将来予測)"
