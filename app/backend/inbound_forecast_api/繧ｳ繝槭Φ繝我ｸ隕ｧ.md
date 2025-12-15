# 実行コマンド一覧
#
# 前提:
# 1. カレントディレクトリは本フォルダ (/works/data/submission_release_20251027) であること
# 2. 必要なライブラリがインストールされていること (pip install -r requirements.txt)

================================================================================
[モデル概要と評価指標]
================================================================================

1. 日次モデル (Daily Model)
   - 使用ファイル:
     - 入力: data/input/20240501-20250422.csv (日次明細), data/input/yoyaku_data.csv (予約)
     - 出力: data/output/final_fast_balanced/model_bundle.joblib (モデル), data/output/tplus1_pred.csv (予測)
   - 評価方法: Walk-Forward Validation (時系列交差検証)
   - 精度指標 (参考値):
     - R2 (決定係数): 0.81 (Total), 0.54 (Sum Only)
     - MAE (平均絶対誤差): 10,347 kg (Total)
     - ※予約情報や品目別モデルの積み上げにより、高い精度を実現しています。

2. 月次モデル (Monthly Gamma + Blend)
   - 使用ファイル:
     - 入力: data/input/01_daily_clean.csv
     - 出力: data/output/gamma_recency_model/blended_future_forecast.csv
   - 評価方法: Cross Validation (交差検証)
   - 精度指標 (参考値):
     - MAE: 63.9 ~ 103.7 ton (Foldにより変動)
     - MAPE: 2.8% ~ 4.6%
     - R2: 0.74 (全体評価)
     - *補足: 月単位での予測精度は比較的高く安定しています。*

3. 週次モデル (Weekly Allocation)
   - 使用ファイル:
     - 入力: data/output/gamma_recency_model/blended_future_forecast.csv (月次予測)
     - 出力: data/output/gamma_recency_model/weekly_allocated_forecast.csv
   - 評価方法: 過去3年間の実績パターンに基づく按分精度の検証 (2024-2025年評価)
   - 精度指標 (参考値):
     - MAE: 34.33 ton
     - WMAPE (加重平均絶対誤差率): 8.1%
     - *補足: 週ごとの変動が大きいためMAPEは高く出ますが、WMAPE(全体量に対する誤差率)は8%程度と良好です。*

4. 月次着地モデル (Monthly Landing Poisson)
   - 使用ファイル:
     - 入力: data/output/monthly_features.csv (日次から集計)
     - 出力: output/prediction_14d.csv (14日時点), output/prediction_21d.csv (21日時点)
   - 評価方法: 過去データを用いたバックテスト (2024年以降)
   - 精度指標 (参考値):
     - [14日時点予測] MAE: 56.28 ton, MAPE: 2.44%
     - [21日時点予測] MAE: 58.18 ton, MAPE: 2.60% (全期間参考値)
     - *補足: 月末に近づくにつれて精度が向上します。いずれも誤差率3%未満と高精度です。*

================================================================================
1. 日次モデル (Daily Model)
================================================================================

### 1-1. 再学習と評価 (クイックモード)
# 動作確認用。学習回数を減らして高速に実行します。
# 日次明細データ(20240501-20250422.csv)と予約データ(yoyaku_data.csv)を使用して学習・推論を行います。
# 実行時間18分10秒
python3 scripts/retrain_and_eval.py --quick

### 1-2. 再学習と評価 (フルモード)
# 本番用。十分な計算リソースがある環境で実行してください。
python3 scripts/retrain_and_eval.py

### 1-3. 推論 (t+1予測)
# 学習済みモデル (model_bundle.joblib) を使用して翌日の予測を行います。
# 予約データ(yoyaku_data.csv)も加味して予測します。
python3 scripts/daily_tplus1_predict.py \
  --bundle data/output/final_fast_balanced/model_bundle.joblib \
  --res-walk-csv data/output/final_fast_balanced/res_walkforward.csv \
  --reserve-csv data/input/yoyaku_data.csv \
  --out-csv data/output/tplus1_pred.csv

### 1-4. 推論 (特定モデル指定)
# 特定の学習済みモデルフォルダを指定して推論を行う例です。
# (例: 20251106_225331 のモデルを使用)
python3 scripts/daily_tplus1_predict.py \
  --bundle data/output/final_fast_balanced/20251106_225331/model_bundle.joblib \
  --res-walk-csv data/output/final_fast_balanced/20251106_225331/res_walkforward.csv \
  --reserve-csv data/input/yoyaku_data.csv \
  --out-csv data/output/tplus1_pred_specific.csv


================================================================================
2. 月次モデル (Monthly Gamma + Blend)
================================================================================

### 2-1. 一括実行 (推奨)
# Gamma Recency モデルとブレンドモデルを順次実行します。
./run_monthly_gamma_blend.sh

### 2-2. 個別実行: Gamma Recency モデルの学習・推論
# ベースとなる月次モデルを実行します。
python3 scripts/gamma_recency_model/gamma_recency_model.py

### 2-3. 個別実行: ブレンドモデルの学習・推論
# Gammaモデルの結果を入力として、Ridge/LGBMで補正・ブレンドを行います。
python3 scripts/gamma_recency_model/blend_lgbm.py

# 出力先: data/output/gamma_recency_model/
#  - blended_prediction_results.csv (評価用)
#  - blended_future_forecast.csv (将来予測)


================================================================================
3. 週次モデル (Weekly Allocation)
================================================================================

### 3-1. 一括実行 (推奨)
# 月次予測結果を用いて週次按分を実行します。
./run_weekly_allocation.sh

### 3-2. 個別実行: 月次予測の週次按分
# 月次ブレンドモデルの将来予測 (blended_future_forecast.csv) を、
# 過去の実績パターンに基づいて週次に按分します。
python3 scripts/weekly_allocation/allocate_monthly_to_weekly_from_blend.py \
  --historical-daily-csv data/input/01_daily_clean.csv \
  --monthly-forecast-csv data/output/gamma_recency_model/blended_future_forecast.csv \
  --out data/output/gamma_recency_model/weekly_allocated_forecast.csv \
  --lookback-years 3


================================================================================
4. 月次着地モデル (Monthly Landing Poisson)
================================================================================

### 4-1. 一括実行 (推奨)
# データ作成、14日版/21日版モデルの学習・保存、推論をまとめて実行します。
./run_monthly_landing_pipeline.sh

### 4-2. 個別実行: 21日版モデルの学習と保存
python3 scripts/monthly_landing_gamma_poisson/run_monthly_landing_gamma_poisson.py \
  --monthly-csv data/output/monthly_features.csv \
  --use-a21 \
  --save-model models/monthly_landing_poisson_21d.pkl

### 4-3. 個別実行: 保存済みモデルでの推論
python3 scripts/monthly_landing_gamma_poisson/run_monthly_landing_gamma_poisson.py \
  --monthly-csv data/output/monthly_features.csv \
  --load-model models/monthly_landing_poisson_21d.pkl \
  --out-csv output/prediction_21d.csv
