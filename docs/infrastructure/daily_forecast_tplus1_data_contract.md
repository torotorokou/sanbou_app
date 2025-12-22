# 日次t+1予測データ契約
**作成日**: 2025-12-18  
**目的**: DBからデータ取得→日次t+1搬入量予測の入出力仕様確定

---

## 0. 調査結果サマリー

### 既存実装の現状
- **入口スクリプト**: `scripts/daily_tplus1_predict.py`
  - 実体は `scripts/serve_predict_model_v4_2_4.py` をラッパー実行
  - 現在の入力：**CSV**（予約CSVは任意）
  - 現在の出力：**CSV**（`tplus1_pred.csv`）
  - DB接続なし（完全にファイルベース）

- **必要な入力データ**:
  1. **モデルバンドル**: `model_bundle.joblib`（学習済みモデル）
  2. **履歴データ**: `res_walkforward.csv`（日次実績の時系列）
  3. **予約データ**: （任意）CSV形式で予約日・台数・固定客を指定

- **出力**:
  - CSV: `date, sum_items_pred, p50, p90, mean_pred, total_pred` 等

---

## 1. DB入力データソース（"正"の定義）

### 1-1. 日次実績（搬入量）

**ビュー/MV**: `mart.v_receive_daily` (VIEW) ← `mart.mv_receive_daily` (MV)

**カラム**:
```sql
ddate               DATE             -- 日付（主キー相当）
receive_net_ton     NUMERIC(18,3)    -- 受入量（トン）★予測対象
receive_vehicle_count INTEGER        -- 車両台数
iso_year            INTEGER          -- ISO年
iso_week            INTEGER          -- ISO週
iso_dow             INTEGER          -- ISO曜日 (1=月, 7=日)
is_business         BOOLEAN          -- 営業日フラグ
is_holiday          BOOLEAN          -- 祝日フラグ
day_type            TEXT             -- 日タイプ ('NORMAL', 'SUNDAY', 'HOLIDAY')
sales_yen           NUMERIC(18,3)    -- 売上金額
avg_weight_kg_per_vehicle NUMERIC   -- 平均積載重量
unit_price_yen_per_kg NUMERIC        -- 単価
source_system       TEXT             -- データソース ('shogun_final', 'shogun_flash', 'king')
```

**取得期間**: 
- `target_date - 365 days` ～ `target_date - 1 day`（直近1年）
- 実運用では最低限必要な期間を調整可（例：90日〜180日）

**使用目的**:
- 予測特徴量の生成（ラグ特徴、移動平均等）
- 曜日パターン、季節性の学習

---

### 1-2. 予約特徴量

**ビュー**: `mart.v_reserve_daily_for_forecast`

**カラム**:
```sql
date                  DATE      -- 予約日
reserve_trucks        INTEGER   -- 予約台数合計
reserve_fixed_trucks  INTEGER   -- 固定客台数
reserve_fixed_ratio   NUMERIC   -- 固定客比率 (0.0～1.0)
source                TEXT      -- データソース ('manual' or 'customer_agg')
```

**取得期間**:
- `target_date`（明日）の1日分
- 存在しない場合は `reserve_trucks=0` 等でデフォルト値を使用

**使用目的**:
- 予約台数による補正
- 固定客比率による需要予測の精度向上

---

## 2. 出力先（結果保存）

### 方針: **B) DBに結果も保存（推奨）**

### 2-1. 予測結果テーブル（新規作成）

**テーブル名**: `forecast.daily_forecast_results`

**カラム設計**:
```sql
CREATE TABLE forecast.daily_forecast_results (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_date         DATE NOT NULL,
    job_id              UUID NOT NULL,  -- jobs.forecast_jobs.job_id への参照
    p50                 NUMERIC(18,3) NOT NULL,  -- 中央値（メイン予測）
    p10                 NUMERIC(18,3),           -- 下側予測
    p90                 NUMERIC(18,3),           -- 上側予測
    unit                TEXT NOT NULL DEFAULT 'ton',
    generated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    input_snapshot      JSONB NOT NULL DEFAULT '{}'::JSONB,
    
    CONSTRAINT uq_daily_forecast_result UNIQUE (target_date, job_id)
);

CREATE INDEX idx_daily_forecast_results_target_date 
    ON forecast.daily_forecast_results(target_date);
CREATE INDEX idx_daily_forecast_results_job_id 
    ON forecast.daily_forecast_results(job_id);
```

**input_snapshot の内容例**:
```json
{
  "actuals_max_date": "2025-12-17",
  "actuals_count": 365,
  "reserve_exists": true,
  "reserve_trucks": 45,
  "reserve_fixed_ratio": 0.67,
  "model_version": "final_fast_balanced",
  "from_date": "2024-12-18",
  "to_date": "2025-12-17"
}
```

---

## 3. 必要な特徴量（最小構成）

### 基本特徴量
1. **日付特徴**:
   - `dow` (曜日 0-6)
   - `month` (月 1-12)
   - `is_holiday` (祝日フラグ)

2. **ラグ特徴**:
   - `lag_1`, `lag_7` (1日前、7日前の実績)
   - `rolling_mean_7` (直近7日の移動平均)

3. **予約特徴**:
   - `reserve_trucks` (予約台数)
   - `reserve_fixed_ratio` (固定客比率)

※既存の `serve_predict_model_v4_2_4.py` に特徴量生成ロジックが存在するため、それを流用

---

## 4. 推論方法

### 優先順位:
1. **既存学習済みモデル** (`model_bundle.joblib`) を使用 ✅
   - `final_fast_balanced/model_bundle.joblib` が存在
   - 推論のみで動作可能

2. （将来）学習を別ジョブに分離

### 推論フロー:
```
1. DBから実績データ取得（365日分）
2. DBから予約データ取得（明日1日分）
3. 特徴量生成（既存ロジック流用）
4. モデル推論（joblib load → predict）
5. 結果をDBに保存
```

---

## 5. ジョブとの統合

### 5-1. ジョブテーブル: `jobs.forecast_jobs`

**既存カラム**:
```sql
job_id          UUID PRIMARY KEY
job_type        TEXT NOT NULL         -- 'daily_tplus1'
status          TEXT NOT NULL         -- 'queued', 'running', 'succeeded', 'failed'
target_date     DATE NOT NULL
input_snapshot  JSONB
output_snapshot JSONB
last_error      TEXT
created_at      TIMESTAMPTZ
updated_at      TIMESTAMPTZ
```

### 5-2. input_snapshot に記録する項目

```json
{
  "actuals_max_date": "2025-12-17",
  "actuals_count": 365,
  "reserve_exists": true,
  "reserve_trucks": 45,
  "reserve_fixed_ratio": 0.67,
  "model_version": "final_fast_balanced",
  "from_date": "2024-12-18",
  "to_date": "2025-12-17",
  "git_sha": "abc123...",          // (optional) コードバージョン
  "image_tag": "v1.2.3"            // (optional) Dockerイメージタグ
}
```

### 5-3. output_snapshot に記録する項目

```json
{
  "result_id": "550e8400-e29b-41d4-a716-446655440000",
  "p50": 125.3,
  "p10": 98.7,
  "p90": 156.2,
  "unit": "ton",
  "generated_at": "2025-12-18T10:30:00Z"
}
```

---

## 6. 動作確認手順

### 6-1. 手動ジョブ投入
```bash
curl -X POST http://localhost:8000/forecast/jobs/daily-tplus1 \
  -H "Content-Type: application/json" \
  -d '{"target_date": "2025-12-19"}'
```

### 6-2. workerログ確認
```bash
docker compose -f docker/docker-compose.dev.yml logs -f inbound_forecast_worker
```

### 6-3. DB確認SQL
```sql
-- ジョブステータス確認
SELECT job_id, job_type, status, target_date, last_error
FROM jobs.forecast_jobs
WHERE job_type = 'daily_tplus1'
ORDER BY created_at DESC
LIMIT 5;

-- 結果確認
SELECT target_date, p50, p10, p90, unit, generated_at
FROM forecast.daily_forecast_results
ORDER BY target_date DESC
LIMIT 5;
```

---

## 7. 既知の未対応（今後の拡張）

1. **精度改善**:
   - より多くの特徴量（天気、イベント等）
   - ハイパーパラメータチューニング

2. **祝日マスタ**:
   - 現在は `is_holiday` をDBから取得するが、祝日テーブルの整備

3. **t+7予測**:
   - 7日先までの予測（別ジョブタイプ）

4. **月次予測**:
   - Gamma-Poisson モデルによる月次予測

5. **学習ジョブの分離**:
   - 定期的な再学習を別workerで実行

6. **結果のAPI公開**:
   - core_api 経由でフロントエンドへ予測結果を配信

---

## 8. 参考資料

- `scripts/daily_tplus1_predict.py`: 現在のCSV版入口
- `scripts/serve_predict_model_v4_2_4.py`: 推論ロジック実体
- `app/backend/core_api/migrations_v2/alembic/versions/20251216_003_add_v_reserve_daily_for_forecast.py`: 予約ビュー
- `mart.mv_receive_daily`: 日次実績MV
- `jobs.forecast_jobs`: ジョブテーブル
