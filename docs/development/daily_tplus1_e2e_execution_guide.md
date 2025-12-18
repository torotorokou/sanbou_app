# DB→学習→t+1予測 E2E実行手順書

**作成日**: 2025-12-18  
**対象環境**: dev（local_dev）  
**目的**: forecast.forecast_jobs に daily_tplus1 ジョブを投入し、DB→retrain_and_eval.py --quick→結果DB保存までの全フローを検証

---

## 前提条件

### 1. 必要なテーブルの確認

```bash
# DB確認
cd /home/koujiro/work_env/22.Work_React/sanbou_app
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db psql -U myuser -d sanbou_dev -c "
SELECT schemaname, tablename 
FROM pg_tables 
WHERE schemaname IN ('forecast', 'stg', 'mart') 
  AND tablename IN ('forecast_jobs', 'daily_forecast_results', 'shogun_final_receive', 'v_reserve_daily_for_forecast')
ORDER BY schemaname, tablename;
"
```

**期待される出力**:
```
schemaname | tablename
-----------+----------------------------
forecast   | daily_forecast_results
forecast   | forecast_jobs
stg        | shogun_final_receive
```

### 2. マイグレーション実行（未実行の場合）

```bash
# 最新マイグレーション確認
docker compose -f docker/docker-compose.dev.yml -p local_dev exec core_api \
  alembic -c /backend/migrations_v2/alembic.ini current

# 未適用の場合
docker compose -f docker/docker-compose.dev.yml -p local_dev exec core_api \
  alembic -c /backend/migrations_v2/alembic.ini upgrade head
```

### 3. Worker起動確認

```bash
# workerコンテナのステータス確認
docker ps | grep inbound_forecast_worker

# workerログ確認
docker compose -f docker/docker-compose.dev.yml -p local_dev logs -f inbound_forecast_worker
```

---

## E2E実行手順

### Step 1: テストデータ準備（stg.shogun_final_receiveにデータが無い場合）

```bash
# データ存在確認
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db psql -U myuser -d sanbou_dev -c "
SELECT 
    COUNT(*) as total_rows,
    MIN(slip_date) as min_date,
    MAX(slip_date) as max_date
FROM stg.shogun_final_receive
WHERE is_deleted = false;
"
```

**出力例**:
```
total_rows | min_date   | max_date
-----------+------------+------------
     12345 | 2024-06-01 | 2025-12-17
```

データが無い場合は、将軍CSVアップロードを実行してください。

### Step 2: ジョブ投入

```sql
-- daily_tplus1 ジョブを投入（明日の予測）
INSERT INTO forecast.forecast_jobs (
    id,
    job_type,
    target_date,
    status,
    priority,
    input_snapshot,
    created_at
) VALUES (
    gen_random_uuid(),
    'daily_tplus1',
    CURRENT_DATE + 1,  -- 明日
    'pending',
    10,
    '{}'::jsonb,
    CURRENT_TIMESTAMP
)
RETURNING id, job_type, target_date, status;
```

**実行方法**:
```bash
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db psql -U myuser -d sanbou_dev <<'EOF'
INSERT INTO forecast.forecast_jobs (
    id, job_type, target_date, status, priority, input_snapshot, created_at
) VALUES (
    gen_random_uuid(), 'daily_tplus1', CURRENT_DATE + 1, 'pending', 10, '{}'::jsonb, CURRENT_TIMESTAMP
)
RETURNING id, job_type, target_date, status;
EOF
```

**期待される出力**:
```
                  id                  | job_type     | target_date | status  
--------------------------------------+--------------+-------------+---------
 a1b2c3d4-e5f6-7890-abcd-1234567890ab | daily_tplus1 | 2025-12-19  | pending
```

→ この `id` をメモしておく（後で使用）

### Step 3: Workerログ監視

```bash
# リアルタイムでログを監視
docker compose -f docker/docker-compose.dev.yml -p local_dev logs -f inbound_forecast_worker
```

**期待されるログフロー**:

```log
[INFO] Polling for pending jobs...
[INFO] Picked up job: a1b2c3d4-e5f6-7890-abcd-1234567890ab, type=daily_tplus1
[INFO] 🚀 Starting daily t+1 forecast with training
[INFO] 📁 Created workspace: /tmp/forecast_jobs/a1b2c3d4-e5f6-7890-abcd-1234567890ab
[INFO] 📊 Exporting actuals: 2024-12-19 to 2025-12-18
[INFO] ✅ Exported 12345 actuals to /tmp/forecast_jobs/a1b2c3d4-.../raw.csv
[INFO] 📅 Exporting reserve: 2025-11-28 to 2025-12-26
[INFO] ✅ Exported 67 reserve records to /tmp/forecast_jobs/a1b2c3d4-.../reserve.csv
[INFO] 🔄 Running retrain_and_eval: python3 /backend/scripts/retrain_and_eval.py --quick ...
[INFO] ✅ retrain_and_eval completed successfully
[INFO] 📈 Prediction result: p50=45.123
[INFO] ✅ Saved prediction result to DB
[INFO] ✅ Daily t+1 forecast (with training) completed and committed
[INFO] Job a1b2c3d4-... transitioned: pending -> processing -> succeeded
```

**処理時間**: 約18〜25分（--quickモード）

### Step 4: DB確認

#### 4-1. ジョブステータス確認

```bash
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db psql -U myuser -d sanbou_dev <<'EOF'
SELECT 
    id,
    job_type,
    target_date,
    status,
    started_at,
    completed_at,
    EXTRACT(EPOCH FROM (completed_at - started_at)) / 60 AS duration_minutes,
    last_error
FROM forecast.forecast_jobs
WHERE job_type = 'daily_tplus1'
ORDER BY created_at DESC
LIMIT 5;
EOF
```

**期待される出力**:
```
                  id                  | job_type     | target_date |  status   | started_at          | completed_at        | duration_minutes | last_error 
--------------------------------------+--------------+-------------+-----------+---------------------+---------------------+------------------+------------
 a1b2c3d4-e5f6-7890-abcd-1234567890ab | daily_tplus1 | 2025-12-19  | succeeded | 2025-12-18 10:00:00 | 2025-12-18 10:18:30 |            18.5  | 
```

#### 4-2. 予測結果確認

```bash
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db psql -U myuser -d sanbou_dev <<'EOF'
SELECT 
    id,
    target_date,
    job_id,
    p50,
    p10,
    p90,
    unit,
    generated_at,
    input_snapshot
FROM forecast.daily_forecast_results
WHERE target_date = CURRENT_DATE + 1
ORDER BY generated_at DESC
LIMIT 1;
EOF
```

**期待される出力**:
```
                  id                  | target_date |              job_id                  |  p50   | p10  | p90  | unit | generated_at        | input_snapshot
--------------------------------------+-------------+--------------------------------------+--------+------+------+------+---------------------+-----------------
 b2c3d4e5-f6g7-8901-bcde-234567890abc | 2025-12-19  | a1b2c3d4-e5f6-7890-abcd-1234567890ab | 45.123 | NULL | NULL | ton  | 2025-12-18 10:18:29 | {...}
```

#### 4-3. input_snapshot詳細確認

```bash
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db psql -U myuser -d sanbou_dev <<'EOF'
SELECT 
    target_date,
    jsonb_pretty(input_snapshot) AS input_snapshot_detail
FROM forecast.daily_forecast_results
WHERE target_date = CURRENT_DATE + 1
ORDER BY generated_at DESC
LIMIT 1;
EOF
```

**期待される出力**:
```json
{
    "actuals_start_date": "2024-12-19",
    "actuals_end_date": "2025-12-18",
    "actuals_count": 12345,
    "reserve_exists": true,
    "reserve_count": 67,
    "model_version": "final_fast_balanced",
    "training_mode": "quick",
    "workspace": "/tmp/forecast_jobs/a1b2c3d4-e5f6-7890-abcd-1234567890ab"
}
```

### Step 5: workspace確認（コンテナ内）

```bash
# workerコンテナに入る
docker compose -f docker/docker-compose.dev.yml -p local_dev exec inbound_forecast_worker bash

# job_id を環境変数にセット（上記Step 2でメモしたID）
export JOB_ID="a1b2c3d4-e5f6-7890-abcd-1234567890ab"

# workspaceディレクトリ確認
ls -lh /tmp/forecast_jobs/$JOB_ID/

# 期待される出力:
# drwxr-xr-x 2 root root 4.0K Dec 18 10:05 out/
# -rw-r--r-- 1 root root 1.2M Dec 18 10:05 raw.csv
# -rw-r--r-- 1 root root 3.5K Dec 18 10:05 reserve.csv
# -rw-r--r-- 1 root root  256 Dec 18 10:18 tplus1_pred.csv
# -rw-r--r-- 1 root root  45K Dec 18 10:18 run.log
```

#### 5-1. raw.csv の先頭確認

```bash
head -5 /tmp/forecast_jobs/$JOB_ID/raw.csv
```

**期待される出力**:
```csv
伝票日付,品名,正味重量
2024-12-19,混合廃棄物,1.234
2024-12-19,木くず,0.567
2024-12-20,混合廃棄物,2.345
2024-12-20,プラスチック類,0.890
```

#### 5-2. reserve.csv の先頭確認

```bash
head -5 /tmp/forecast_jobs/$JOB_ID/reserve.csv
```

**期待される出力**:
```csv
予約日,台数,固定客
2025-11-28,45,30
2025-11-29,50,35
2025-11-30,48,32
2025-12-01,52,36
```

#### 5-3. 予測結果CSV確認

```bash
cat /tmp/forecast_jobs/$JOB_ID/tplus1_pred.csv
```

**期待される出力**:
```csv
date,y_pred
2025-12-19,45.123
```

#### 5-4. ログ末尾確認

```bash
tail -20 /tmp/forecast_jobs/$JOB_ID/run.log
```

**期待される出力**:
```
Training completed.
Starting prediction...
Prediction completed.
```

---

## トラブルシューティング

### エラー1: "No actuals found between ..."

**原因**: stg.shogun_final_receive にデータが無い

**対処**:
1. 将軍CSVアップロード実行
2. または、手動でテストデータをINSERT

### エラー2: "retrain_and_eval.py failed with rc=1"

**原因**: 学習スクリプトの実行エラー

**対処**:
1. run.log の末尾を確認: `cat /tmp/forecast_jobs/$JOB_ID/run.log`
2. 入力データの確認: raw.csv / reserve.csv の内容を確認
3. retrain_and_eval.py を手動実行してデバッグ:
   ```bash
   cd /backend
   python3 scripts/retrain_and_eval.py --help
   ```

### エラー3: "Prediction output not found"

**原因**: retrain_and_eval.py は成功したが、出力CSVが生成されなかった

**対処**:
1. --pred-out-csv のパスが正しいか確認
2. daily_tplus1_predict.py の実装を確認（--start-date引数に対応しているか）

### エラー4: Job status が "processing" で止まる

**原因**: タイムアウトまたはハングアップ

**対処**:
1. Workerログを確認: どの処理で止まっているか
2. タイムアウト値を増やす: DEFAULT_TIMEOUT = 3600 (60分)
3. --quick以外のモードは使わない（初期実装では非対応）

---

## 成功判定チェックリスト

- [ ] Step 2: ジョブ投入成功（pending状態で登録）
- [ ] Step 3: Workerログに「🚀 Starting daily t+1 forecast with training」表示
- [ ] Step 3: Workerログに「✅ retrain_and_eval completed successfully」表示
- [ ] Step 3: Workerログに「✅ Saved prediction result to DB」表示
- [ ] Step 4-1: forecast.forecast_jobs.status = 'succeeded'
- [ ] Step 4-2: forecast.daily_forecast_results にレコード存在
- [ ] Step 4-2: p50 に数値が入っている
- [ ] Step 4-3: input_snapshot に actuals_count, reserve_count が記録
- [ ] Step 5: workspace に raw.csv, reserve.csv, tplus1_pred.csv, run.log が存在

---

## 変更ファイル一覧

### 1. スクリプト変更

| ファイル | 変更内容 |
|---------|---------|
| [app/backend/inbound_forecast_worker/scripts/retrain_and_eval.py](../app/backend/inbound_forecast_worker/scripts/retrain_and_eval.py) | 引数追加: --raw-csv, --reserve-csv, --out-dir, --pred-out-csv, --start-date |

**追加引数一覧**:
```
--raw-csv <path>           # 学習入力CSV（品目別形式: 伝票日付,品名,正味重量）
--reserve-csv <path>       # 予約CSV（予約日,台数,固定客）
--out-dir <dir>            # 出力ディレクトリ（bundle/res_walkforward出力先）
--pred-out-csv <path>      # t+1予測結果CSV出力先
--start-date <YYYY-MM-DD>  # 予測基準日（省略時は最新データ日の翌日）
```

### 2. core_api Ports（抽象インターフェース）

| ファイル | 役割 |
|---------|------|
| [app/backend/core_api/app/core/ports/inbound_actuals_export_port.py](../app/backend/core_api/app/core/ports/inbound_actuals_export_port.py) | 品目別日次実績エクスポート |
| [app/backend/core_api/app/core/ports/reserve_export_port.py](../app/backend/core_api/app/core/ports/reserve_export_port.py) | 日次予約エクスポート |
| [app/backend/core_api/app/core/ports/daily_forecast_result_repository_port.py](../app/backend/core_api/app/core/ports/daily_forecast_result_repository_port.py) | 日次予測結果保存 |

### 3. core_api Adapters（実装）

| ファイル | SQL対象 | 役割 |
|---------|---------|------|
| [app/backend/core_api/app/infra/adapters/forecast/inbound_actuals_exporter.py](../app/backend/core_api/app/infra/adapters/forecast/inbound_actuals_exporter.py) | stg.shogun_final_receive | 品目別データ→CSV（kg→ton変換） |
| [app/backend/core_api/app/infra/adapters/forecast/reserve_exporter.py](../app/backend/core_api/app/infra/adapters/forecast/reserve_exporter.py) | mart.v_reserve_daily_for_forecast | 予約データ→CSV |
| [app/backend/core_api/app/infra/adapters/forecast/daily_forecast_result_repository.py](../app/backend/core_api/app/infra/adapters/forecast/daily_forecast_result_repository.py) | forecast.daily_forecast_results | 予測結果INSERT |

### 4. inbound_forecast_worker UseCase

| ファイル | 役割 |
|---------|------|
| [app/backend/inbound_forecast_worker/app/application/run_daily_tplus1_forecast_with_training.py](../app/backend/inbound_forecast_worker/app/application/run_daily_tplus1_forecast_with_training.py) | DB→学習→予測のE2E実行 |

### 5. inbound_forecast_worker Executor

| ファイル | 変更内容 |
|---------|---------|
| [app/backend/inbound_forecast_worker/app/job_executor.py](../app/backend/inbound_forecast_worker/app/job_executor.py) | execute_daily_tplus1()に use_training=True を追加 |

---

## 生成CSVサンプル

### raw.csv（学習用、先頭5行）

```csv
伝票日付,品名,正味重量
2024-12-19,混合廃棄物,1.234
2024-12-19,木くず,0.567
2024-12-19,プラスチック類,0.890
2024-12-20,混合廃棄物,2.345
```

### reserve.csv（予約用、先頭5行）

```csv
予約日,台数,固定客
2025-11-28,45,30
2025-11-29,50,35
2025-11-30,48,32
2025-12-01,52,36
```

---

## 既知の課題

### 1. 処理時間

- **現状**: --quick で約18分（README記載）
- **対応**: タイムアウトを30分に設定済み
- **将来**: フル学習は別ジョブ（週次バッチ）で実施

### 2. workspace クリーンアップ

- **現状**: /tmp配下に蓄積（手動削除）
- **対応**: 定期クリーンアップスクリプトを実装（Phase 5）

### 3. p10/p90の未実装

- **現状**: retrain_and_eval.py が区間予測を出力していない
- **対応**: p50のみ保存、p10/p90はNULL

### 4. 同時実行制御

- **現状**: 複数ジョブが同時実行される可能性
- **対応**: job_pollerでロック機構を実装（Phase 5）

---

## Prod運用方針

### Dev環境

- [x] --quick で動作確認
- [x] エラーハンドリング確認
- [x] workspace の確認

### Stg環境

- [ ] --quick で精度確認
- [ ] 失敗時の挙動検証（last_error保存、worker継続）
- [ ] 負荷テスト（複数ジョブ投入）

### Prod環境

- [ ] 初期: --quick で運用開始
- [ ] 安定後: 学習ジョブを週次バッチ化、日次は推論のみに移行

---

**作成日**: 2025-12-18  
**最終更新**: 2025-12-18  
**バージョン**: 1.0
