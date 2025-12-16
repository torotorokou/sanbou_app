# 予測タイプ一覧とWorker実行要件

## 概要
inbound_forecast_worker で実行可能な予測タイプと、それぞれの実行に必要な前提条件を整理したドキュメント。

---

## 1. 日次予測 t+1 (daily_tplus1)

### 概要
- **目的:** 翌日の搬入量を予測
- **job_type:** `daily_tplus1`
- **実行スクリプト:** `scripts/daily_tplus1_predict.py`
- **実装状況:** ✅ 実装済み (A-3b)

### 実行に必要な前提

#### 必須ファイル
1. **学習済みモデル**
   - パス: `/backend/models/final_fast_balanced/model_bundle.joblib`
   - 内容: 学習済みの日次予測モデル（品目別モデル含む）
   - 生成方法: `scripts/retrain_and_eval.py` で再学習

2. **履歴データ**
   - パス: `/backend/models/final_fast_balanced/res_walkforward.csv`
   - 内容: Walk-Forward Validation の結果（履歴の末尾データ）
   - 用途: 予測の起点となる履歴情報

3. **予約データ (オプション)**
   - パス: `/backend/data/input/yoyaku_data.csv`
   - 内容: 予約台数・固定客情報
   - 省略時: 予約なし（ゼロ）として予測

#### 出力
- パス: `/backend/output/tplus1_pred_{target_date}.csv`
- 形式: CSV（日次予測結果）

#### コマンド例
```bash
python3 /backend/scripts/daily_tplus1_predict.py \
  --bundle /backend/models/final_fast_balanced/model_bundle.joblib \
  --res-walk-csv /backend/models/final_fast_balanced/res_walkforward.csv \
  --out-csv /backend/output/tplus1_pred_2025-12-17.csv \
  --start-date 2025-12-17
```

#### 実行時間
- 約1〜2分（予測のみ）

---

## 2. 日次予測 t+7 (daily_tplus7)

### 概要
- **目的:** 7日後の搬入量を予測
- **job_type:** `daily_tplus7`
- **実行スクリプト:** `scripts/serve_predict_model_v4_2_4.py` (future-days=7)
- **実装状況:** ⏳ 未実装（ホワイトリストには登録済み）

### 実行に必要な前提

#### 必須ファイル
- daily_tplus1 と同じモデルファイルを使用
- `--future-days 7` オプションで7日分予測

#### 出力
- パス: `/backend/output/tplus7_pred_{target_date}.csv`
- 形式: CSV（7日分の予測結果）

#### コマンド例
```bash
python3 /backend/scripts/serve_predict_model_v4_2_4.py \
  --bundle /backend/models/final_fast_balanced/model_bundle.joblib \
  --res-walk-csv /backend/models/final_fast_balanced/res_walkforward.csv \
  --out-csv /backend/output/tplus7_pred_2025-12-17.csv \
  --future-days 7 \
  --start-date 2025-12-17
```

#### 実行時間
- 約5〜10分（7日分のループ予測）

---

## 3. 月次予測 Gamma Recency (monthly_gamma)

### 概要
- **目的:** 月次搬入量を Gamma-Recency モデルで予測
- **job_type:** `monthly_gamma`
- **実行スクリプト:** `scripts/gamma_recency_model/gamma_recency_model.py`
- **実装状況:** ⏳ 未実装（ホワイトリストには登録済み）

### 実行に必要な前提

#### 必須ファイル
1. **日次クリーンデータ**
   - パス: `/backend/data/input/01_daily_clean.csv`
   - 内容: 過去の日次搬入実績データ（クリーニング済み）
   - 必須カラム: date, weight, customer_id など

#### 出力
- パス: `/backend/data/output/gamma_recency_model/gamma_forecast.csv`
- 形式: CSV（月次予測結果）

#### コマンド例
```bash
python3 /backend/scripts/gamma_recency_model/gamma_recency_model.py \
  --input-csv /backend/data/input/01_daily_clean.csv \
  --output-csv /backend/data/output/gamma_recency_model/gamma_forecast.csv
```

#### 実行時間
- 約10〜20分（交差検証含む）

#### 注意事項
- 月次予測 Blend (monthly_blend) の前提となるため、先に実行必要

---

## 4. 月次予測 Blend (monthly_blend)

### 概要
- **目的:** Gamma-Recency 予測を Ridge/LGBM で補正・ブレンド
- **job_type:** `monthly_blend`（または weekly の前処理として実行）
- **実行スクリプト:** `scripts/gamma_recency_model/blend_lgbm.py`
- **実装状況:** ⏳ 未実装

### 実行に必要な前提

#### 必須ファイル
1. **Gamma-Recency 予測結果**
   - パス: `/backend/data/output/gamma_recency_model/gamma_forecast.csv`
   - 生成元: monthly_gamma の実行結果

2. **日次クリーンデータ**
   - パス: `/backend/data/input/01_daily_clean.csv`
   - 用途: ブレンドモデルの学習

#### 出力
- パス: `/backend/data/output/gamma_recency_model/blended_future_forecast.csv`
- 形式: CSV（ブレンド後の月次予測）

#### コマンド例
```bash
python3 /backend/scripts/gamma_recency_model/blend_lgbm.py \
  --gamma-forecast /backend/data/output/gamma_recency_model/gamma_forecast.csv \
  --daily-clean /backend/data/input/01_daily_clean.csv \
  --output-csv /backend/data/output/gamma_recency_model/blended_future_forecast.csv
```

#### 実行時間
- 約5〜10分

---

## 5. 週次予測 按分 (weekly)

### 概要
- **目的:** 月次予測を週次に按分
- **job_type:** `weekly`
- **実行スクリプト:** `scripts/weekly_allocation/allocate_monthly_to_weekly_from_blend.py`
- **実装状況:** ⏳ 未実装（ホワイトリストには登録済み）

### 実行に必要な前提

#### 必須ファイル
1. **月次ブレンド予測結果**
   - パス: `/backend/data/output/gamma_recency_model/blended_future_forecast.csv`
   - 生成元: monthly_blend の実行結果

2. **日次クリーンデータ（履歴）**
   - パス: `/backend/data/input/01_daily_clean.csv`
   - 用途: 過去3年間の実績パターンから按分比率を計算

#### 出力
- パス: `/backend/data/output/gamma_recency_model/weekly_allocated_forecast.csv`
- 形式: CSV（週次予測結果）

#### コマンド例
```bash
python3 /backend/scripts/weekly_allocation/allocate_monthly_to_weekly_from_blend.py \
  --historical-daily-csv /backend/data/input/01_daily_clean.csv \
  --monthly-forecast-csv /backend/data/output/gamma_recency_model/blended_future_forecast.csv \
  --out /backend/data/output/gamma_recency_model/weekly_allocated_forecast.csv \
  --lookback-years 3
```

#### 実行時間
- 約2〜5分

---

## 6. 月次着地 14日時点 (monthly_landing_14d)

### 概要
- **目的:** 月の14日時点での着地予測
- **job_type:** `monthly_landing_14d`
- **実行スクリプト:** `scripts/monthly_landing_gamma_poisson/run_monthly_landing_gamma_poisson.py`
- **実装状況:** ⏳ 未実装（ホワイトリストには登録済み）

### 実行に必要な前提

#### 必須ファイル
1. **月次特徴量データ**
   - パス: `/backend/data/output/monthly_features.csv`
   - 内容: 日次データから集計した月次特徴量
   - 生成方法: 日次データの前処理スクリプト

2. **学習済みモデル（オプション）**
   - パス: `/backend/models/monthly_landing_poisson_14d.pkl`
   - 事前学習済みモデルがあれば使用可能

#### 出力
- パス: `/backend/output/prediction_14d_{target_month}.csv`
- 形式: CSV（月次着地予測結果）

#### コマンド例
```bash
# 学習済みモデルで推論
python3 /backend/scripts/monthly_landing_gamma_poisson/run_monthly_landing_gamma_poisson.py \
  --monthly-csv /backend/data/output/monthly_features.csv \
  --load-model /backend/models/monthly_landing_poisson_14d.pkl \
  --out-csv /backend/output/prediction_14d.csv

# モデル学習から実行
python3 /backend/scripts/monthly_landing_gamma_poisson/run_monthly_landing_gamma_poisson.py \
  --monthly-csv /backend/data/output/monthly_features.csv \
  --use-a14 \
  --out-csv /backend/output/prediction_14d.csv
```

#### 実行時間
- 推論のみ: 約1分
- 学習含む: 約5〜10分

---

## 7. 月次着地 21日時点 (monthly_landing_21d)

### 概要
- **目的:** 月の21日時点での着地予測
- **job_type:** `monthly_landing_21d`
- **実行スクリプト:** `scripts/monthly_landing_gamma_poisson/run_monthly_landing_gamma_poisson.py`
- **実装状況:** ⏳ 未実装（ホワイトリストには登録済み）

### 実行に必要な前提

#### 必須ファイル
- monthly_landing_14d と同じ構成
- `--use-a21` オプションで21日版モデルを使用

#### 出力
- パス: `/backend/output/prediction_21d_{target_month}.csv`
- 形式: CSV（月次着地予測結果）

#### コマンド例
```bash
# 学習済みモデルで推論
python3 /backend/scripts/monthly_landing_gamma_poisson/run_monthly_landing_gamma_poisson.py \
  --monthly-csv /backend/data/output/monthly_features.csv \
  --load-model /backend/models/monthly_landing_poisson_21d.pkl \
  --out-csv /backend/output/prediction_21d.csv

# モデル学習から実行
python3 /backend/scripts/monthly_landing_gamma_poisson/run_monthly_landing_gamma_poisson.py \
  --monthly-csv /backend/data/output/monthly_features.csv \
  --use-a21 \
  --out-csv /backend/output/prediction_21d.csv
```

#### 実行時間
- 推論のみ: 約1分
- 学習含む: 約5〜10分

---

## 実装優先順位

### Phase 1（完了）
- ✅ daily_tplus1: 日次予測 t+1（最も利用頻度が高い）

### Phase 2（推奨順）
1. **weekly**: 週次予測按分
   - 理由: 短期計画に必要、月次予測の依存関係含む
   - 依存: monthly_gamma → monthly_blend → weekly

2. **monthly_landing_14d / 21d**: 月次着地予測
   - 理由: 月次実績管理に必要、独立実行可能

### Phase 3
3. **daily_tplus7**: 7日先予測
   - 理由: daily_tplus1 の拡張、同じモデル使用

---

## 共通の前提条件

### 環境変数
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`: DB接続情報
- `DATABASE_URL`: 自動構築（backend_shared使用）

### Pythonパッケージ
- pandas==2.2.3
- numpy
- scikit-learn>=1.5.0
- lightgbm>=4.0.0
- scipy>=1.14.0
- joblib

### ディレクトリ構造
```
/backend/
├── scripts/              # 実行スクリプト
├── models/               # 学習済みモデル
├── data/
│   ├── input/           # 入力データ
│   └── output/          # 中間・出力データ
└── output/              # 最終出力
```

---

## トラブルシューティング

### モデルファイルが見つからない
```
Error: Model bundle not found: /backend/models/final_fast_balanced/model_bundle.joblib
```
**対処:** `scripts/retrain_and_eval.py` で再学習してモデルを生成

### 履歴データが不足
```
Error: Not enough historical data for prediction
```
**対処:** `res_walkforward.csv` に十分な履歴データがあるか確認（最低30日分推奨）

### 依存ファイルが見つからない
```
Error: File not found: /backend/data/output/gamma_recency_model/blended_future_forecast.csv
```
**対処:** 依存する前段のジョブ（monthly_gamma → monthly_blend）を先に実行

---

## 参考資料
- 実行コマンド詳細: [docs.md](../app/backend/inbound_forecast_worker/docs.md)
- Worker実装: [app/job_executor.py](../app/backend/inbound_forecast_worker/app/job_executor.py)
- API仕様: [forecast/router.py](../app/backend/core_api/app/api/routers/forecast/router.py)
