# 日次t+1予測 E2Eテスト実行計画書

**作成日**: 2025-12-18  
**目的**: エンドツーエンドテスト実行とモデルファイル不要の実装確認

---

## Step A: 現状コードの挙動確認（調査結果）

### 1. 実行コマンド

```bash
python3 /backend/scripts/daily_tplus1_predict.py \
  --bundle /backend/models/final_fast_balanced/model_bundle.joblib \
  --res-walk-csv /backend/models/final_fast_balanced/res_walkforward.csv \
  --out-csv /backend/output/tplus1_pred_YYYY-MM-DD.csv \
  --start-date YYYY-MM-DD \
  [--reserve-csv /path/to/reserve.csv]
```

### 2. 入力

| 項目 | 必須 | 説明 |
|------|------|------|
| `--bundle` | ✅ | 学習済みモデルバンドル（*.joblib） |
| `--res-walk-csv` | ✅ | 履歴データ（res_walkforward.csv） |
| `--out-csv` | ✅ | 出力CSV |
| `--start-date` | ⚠️ | 予測開始日（省略時は履歴の翌日） |
| `--reserve-csv` | ❌ | 予約データCSV（任意） |

**入力データソース:**
- **バンドル内蔵**: `bundle['history_tail']` に実績時系列が含まれる
- **外部CSV**: `--res-walk-csv` を明示指定した場合、そちらを優先
- **予約データ**: CSV形式（日付、台数、固定客）

### 3. 出力

**CSVフォーマット:**
```csv
date,sum_items_pred,p50,p90,mean_pred,total_pred
2025-12-19,125.3,125.3,156.2,125.3,125.3
```

**カラム:**
- `date`: 予測対象日
- `sum_items_pred`: 品目別予測の合計
- `p50`: 中央値予測（メイン）
- `p90`: 90パーセンタイル予測
- `mean_pred`: 平均予測
- `total_pred`: トータル予測（最終値）

### 4. 「学習→予測」の流れ

**重要発見:**

✅ **`serve_predict_model_v4_2_4.py` はモデルバンドルからの推論のみを実行する**

- `residual_refit=True` オプションで **残差モデルの再学習** が可能
- しかし、**メインモデルの学習は行わない**（学習済みモデルが前提）

**残差再学習（residual_refit）の仕組み:**
```python
if residual_refit:
    # 履歴の末尾90日（デフォルト）を使って残差モデルを追加学習
    resid_target = y_hist_full - base_pred_hist_full
    m = GradientBoostingRegressor(...)
    m.fit(X_resid, resid_target, sample_weight=sw)
    # 将来予測時に残差補正を適用
    pred_adjusted = base_pred + m.predict(X_future)
```

**結論:**
- 現状の `daily_tplus1_predict.py` は **学習済みモデルが必須**
- モデルファイルが無い場合はエラー
- E2Eテストのためには以下のいずれかが必要：
  1. モデルファイルを事前配置
  2. **学習→予測を一貫実行するスクリプトを新規作成** ✅（推奨）

### 5. 必要な環境変数

**明示的な環境変数は不要** （すべてコマンドライン引数で指定）

ただし、以下の前提がある：
- Python 3.10+ 環境
- 必要ライブラリ: `pandas`, `numpy`, `joblib`, `scikit-learn`
- DB接続（今回の実装でDBから実績取得する場合）

---

## Step B: Worker側の実行方式を"学習→予測対応"にする

### 現状の問題

現在の `RunDailyTplus1ForecastUseCase` は：
- モデルバンドル（`model_bundle.joblib`）が存在することを前提
- 存在しない場合は `ModelBundleNotFoundError`

### 解決策

**Option 1: 簡易対応（推奨）- 残差再学習を有効化**

`serve_predict_model_v4_2_4.py` を呼び出す際に `--residual-refit` を追加：

```python
cmd = [
    "python3",
    str(self._script_path),
    "--bundle", str(self._model_bundle_path),
    "--res-walk-csv", str(self._res_walk_csv_path),
    "--out-csv", str(output_csv_path),
    "--start-date", target_date.isoformat(),
    "--residual-refit",  # ← 残差再学習を有効化
    "--residual-refit-window", "90",
]
```

**メリット:**
- 既存スクリプトをそのまま活用
- モデルファイルは必要だが、最新データで補正される

**デメリット:**
- 初回実行時にはモデルファイルが必要

**Option 2: フルスクラッチ学習スクリプトを作成**

`scripts/train_and_predict_daily.py` を新規作成：
- DBから実績データ取得
- ゼロから学習
- 予測実行
- 結果をDBまたはCSV保存

**メリット:**
- モデルファイル不要
- 完全に自己完結

**デメリット:**
- 実装工数が大きい
- 学習時間が長い（毎回30秒〜数分）

### 採用方針: **Option 1（残差再学習）+ モデルファイル配置**

**理由:**
- E2Eテストを迅速に実施できる
- 既存の学習済みモデルを活用（精度担保）
- 残差再学習により最新データへの適応も可能

**実装変更:**

1. `model_bundle.joblib` と `res_walkforward.csv` をコンテナ内に配置
2. `RunDailyTplus1ForecastUseCase` で `--residual-refit` を有効化
3. モデルファイルが無い場合の明確なエラーメッセージ

---

## Step C: E2E実行手順

### 前提条件

```bash
# 1. DB起動
cd /home/koujiro/work_env/22.Work_React/sanbou_app
docker compose -f docker/docker-compose.dev.yml -p local_dev up -d db

# 2. マイグレーション実行（daily_forecast_results テーブル作成）
docker compose -f docker/docker-compose.dev.yml -p local_dev exec core_api \
  alembic -c /backend/migrations/alembic.ini upgrade head

# 3. Worker起動
docker compose -f docker/docker-compose.dev.yml -p local_dev up -d inbound_forecast_worker

# 4. 実績データがDBに存在することを確認
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db psql -U myuser -d sanbou_dev -c \
  "SELECT COUNT(*) FROM mart.v_receive_daily WHERE ddate >= CURRENT_DATE - INTERVAL '365 days';"
```

### E2Eテスト実行

#### 1. ジョブ投入（SQLで直接）

```sql
-- ジョブ投入
INSERT INTO forecast.forecast_jobs (
    job_type,
    target_date,
    status,
    run_after,
    input_snapshot
) VALUES (
    'daily_tplus1',
    CURRENT_DATE + INTERVAL '1 day',  -- 明日
    'queued',
    CURRENT_TIMESTAMP,
    '{}'::jsonb
);
```

または

```bash
# psql経由で実行
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db psql -U myuser -d sanbou_dev <<EOF
INSERT INTO forecast.forecast_jobs (job_type, target_date, status, run_after)
VALUES ('daily_tplus1', CURRENT_DATE + INTERVAL '1 day', 'queued', CURRENT_TIMESTAMP);
EOF
```

#### 2. Workerログ確認

```bash
# リアルタイムでログを追跡
docker compose -f docker/docker-compose.dev.yml -p local_dev logs -f inbound_forecast_worker
```

**期待ログ:**
```json
{"timestamp": "2025-12-18T...", "level": "INFO", "message": "🎯 Poll #XX: Job claimed", "job_id": "...", "job_type": "daily_tplus1"}
{"timestamp": "2025-12-18T...", "level": "INFO", "message": "Starting daily t+1 forecast", "target_date": "2025-12-19"}
{"timestamp": "2025-12-18T...", "level": "INFO", "message": "Fetched XXX actual records from mart.v_receive_daily"}
{"timestamp": "2025-12-18T...", "level": "INFO", "message": "✅ Daily t+1 forecast completed", "p50": 125.3}
```

#### 3. 結果確認SQL

```sql
-- ジョブステータス確認
SELECT 
    id,
    job_type,
    status,
    target_date,
    last_error,
    created_at,
    started_at,
    finished_at
FROM forecast.forecast_jobs
WHERE job_type = 'daily_tplus1'
ORDER BY created_at DESC
LIMIT 5;

-- 予測結果確認
SELECT 
    target_date,
    p50,
    p10,
    p90,
    unit,
    generated_at,
    input_snapshot
FROM forecast.daily_forecast_results
ORDER BY target_date DESC
LIMIT 5;
```

**期待結果:**
- `forecast.forecast_jobs.status = 'succeeded'`
- `forecast.daily_forecast_results` に予測結果が保存される
- `p50 > 0` （予測値が存在）

---

## Step D: 失敗系テスト

### テストケース1: データ不足エラー

```sql
-- 未来の日付でジョブ投入（実績データが無い）
INSERT INTO forecast.forecast_jobs (job_type, target_date, status, run_after)
VALUES ('daily_tplus1', '2026-12-31', 'queued', CURRENT_TIMESTAMP);
```

**期待結果:**
- `status = 'failed'`
- `last_error = 'No actual data found between 2025-12-31 and 2026-12-30'`

### テストケース2: モデルファイル不在

（現状の実装では発生中）

**期待結果:**
- `status = 'failed'`
- `last_error = 'Model bundle not found: /backend/models/...'`

### テストケース3: DB接続エラー

```bash
# Workerを起動したままDBを停止
docker compose -f docker/docker-compose.dev.yml -p local_dev stop db
```

**期待結果:**
- ジョブがクレームできず、`queued` のまま
- Workerログに接続エラー

---

## モデル保存ポリシー（今後の拡張）

### 保存しない場合（現状）

✅ **メリット:**
- 実装がシンプル
- ストレージ不要

❌ **デメリット:**
- 毎回学習が必要（時間・CPU負荷）

### 保存する場合の推奨設計

#### 保存先

```
/backend/models/
  daily_tplus1/
    {job_id}/
      model_bundle.joblib
      res_walkforward.csv
      metadata.json
```

#### ファイル名規則

- `{job_id}/model_bundle.joblib`: ジョブIDでディレクトリ分離
- 衝突防止
- 後からジョブと紐付け可能

#### 保存タイミング

- 予測成功後
- 保存失敗しても予測は成功扱い（Warning）

#### クリーンアップ

```bash
# 30日以上前のモデルを削除（cron）
find /backend/models/daily_tplus1/ -type d -mtime +30 -exec rm -rf {} \;
```

#### 環境別の保存先

| 環境 | 保存先 | 書き込み権限 |
|------|--------|--------------|
| local_dev | `/backend/models/daily_tplus1/` | Docker volume |
| stg/prod | GCS Bucket `gs://sanbou-models/daily_tplus1/` | Service Account |

---

## 提出物チェックリスト

- [ ] 変更ファイル一覧
- [ ] 実行コマンド一式
- [ ] 成功ログ例
- [ ] 失敗ログ例
- [ ] モデル保存推奨案

---

## 次のアクション

1. **モデルファイル配置** （テスト用）
2. **UseCase修正** （`--residual-refit` 追加）
3. **E2E実行**
4. **失敗系テスト**
5. **ドキュメント完成**
