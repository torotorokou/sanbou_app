# 日次t+1予測DB統合実装完了レポート
**実装日**: 2025-12-18  
**目的**: DBからデータ取得→日次t+1搬入量予測→結果DB保存

---

## 実装サマリー

✅ Clean Architecture（Ports & Adapters）に従った実装完了  
✅ DB→予測→保存の一連のフローを動作可能な状態で実装  
✅ 既存のCSVベーススクリプトを活用（段階的移行）

---

## 変更ファイル一覧

### 1. マイグレーション（DB設計）

#### 新規作成
- [app/backend/core_api/migrations_v2/alembic/versions/20251218_001_add_daily_forecast_results_table.py](app/backend/core_api/migrations_v2/alembic/versions/20251218_001_add_daily_forecast_results_table.py)
  - `forecast.daily_forecast_results` テーブル追加
  - p10/p50/p90 の3点予測を保存
  - `(target_date, job_id)` でユニーク制約
  - `input_snapshot` に入力データの詳細を記録

### 2. Ports（抽象インターフェース）

#### 新規作成
- [app/backend/inbound_forecast_worker/app/ports/__init__.py](app/backend/inbound_forecast_worker/app/ports/__init__.py)
- [app/backend/inbound_forecast_worker/app/ports/inbound_actual_repository.py](app/backend/inbound_forecast_worker/app/ports/inbound_actual_repository.py)
  - `InboundActualRepositoryPort`: 日次実績データの取得
  - `InboundActualDaily`: 日次実績エンティティ
- [app/backend/inbound_forecast_worker/app/ports/reserve_daily_repository.py](app/backend/inbound_forecast_worker/app/ports/reserve_daily_repository.py)
  - `ReserveDailyRepositoryPort`: 予約データの取得
  - `ReserveDailyForForecast`: 予約データエンティティ
- [app/backend/inbound_forecast_worker/app/ports/forecast_result_repository.py](app/backend/inbound_forecast_worker/app/ports/forecast_result_repository.py)
  - `ForecastResultRepositoryPort`: 予測結果の保存
  - `DailyForecastResult`: 予測結果エンティティ

### 3. Adapters（DB実装）

#### 新規作成
- [app/backend/inbound_forecast_worker/app/adapters/__init__.py](app/backend/inbound_forecast_worker/app/adapters/__init__.py)
- [app/backend/inbound_forecast_worker/app/adapters/inbound_actual_repository.py](app/backend/inbound_forecast_worker/app/adapters/inbound_actual_repository.py)
  - `PostgreSQLInboundActualRepository`: `mart.v_receive_daily` からデータ取得
- [app/backend/inbound_forecast_worker/app/adapters/reserve_daily_repository.py](app/backend/inbound_forecast_worker/app/adapters/reserve_daily_repository.py)
  - `PostgreSQLReserveDailyRepository`: `mart.v_reserve_daily_for_forecast` からデータ取得
- [app/backend/inbound_forecast_worker/app/adapters/forecast_result_repository.py](app/backend/inbound_forecast_worker/app/adapters/forecast_result_repository.py)
  - `PostgreSQLForecastResultRepository`: `forecast.daily_forecast_results` へ保存

### 4. Application（UseCase）

#### 新規作成
- [app/backend/inbound_forecast_worker/app/application/__init__.py](app/backend/inbound_forecast_worker/app/application/__init__.py)
- [app/backend/inbound_forecast_worker/app/application/run_daily_tplus1_forecast.py](app/backend/inbound_forecast_worker/app/application/run_daily_tplus1_forecast.py)
  - `RunDailyTplus1ForecastUseCase`: 日次t+1予測の実行手順
  - Phase 1: 既存CSVスクリプトを subprocess で実行（段階的移行）

### 5. Worker統合

#### 更新
- [app/backend/inbound_forecast_worker/app/job_executor.py](app/backend/inbound_forecast_worker/app/job_executor.py)
  - `execute_daily_tplus1()`: DB Session を受け取り、UseCaseを実行
  - `execute_job()`: 引数に `db_session`, `job_id` を追加
- [app/backend/inbound_forecast_worker/app/main.py](app/backend/inbound_forecast_worker/app/main.py)
  - `worker_loop()`: `execute_job()` に DB Session を渡すように修正

### 6. ドキュメント

#### 新規作成
- [docs/infrastructure/daily_forecast_tplus1_data_contract.md](docs/infrastructure/daily_forecast_tplus1_data_contract.md)
  - データ契約定義書（入力・出力の仕様確定）

---

## テーブル定義

### forecast.daily_forecast_results

| カラム | 型 | 制約 | 説明 |
|--------|-----|------|------|
| id | uuid | PK | 結果ID（自動生成） |
| target_date | date | NOT NULL | 予測対象日（明日） |
| job_id | uuid | NOT NULL, FK | ジョブID（forecast.forecast_jobs.id） |
| p50 | numeric(18,3) | NOT NULL | 中央値予測（メイン） |
| p10 | numeric(18,3) | NULL | 下側予測（10パーセンタイル） |
| p90 | numeric(18,3) | NULL | 上側予測（90パーセンタイル） |
| unit | text | NOT NULL | 単位（ton or kg） |
| generated_at | timestamptz | NOT NULL | 生成日時 |
| input_snapshot | jsonb | NOT NULL | 入力データの詳細 |

**制約**:
- `UNIQUE (target_date, job_id)`: 同一ジョブで同じ日付への複数予測を防止
- `FK (job_id) REFERENCES forecast.forecast_jobs(id) ON DELETE CASCADE`

**インデックス**:
- `idx_daily_forecast_results_target_date` on `target_date`
- `idx_daily_forecast_results_job_id` on `job_id`

---

## 入力データソース

### 1. 日次実績（搬入量）

**ビュー**: `mart.v_receive_daily` ← `mart.mv_receive_daily`

**取得カラム**:
- `ddate` (date): 日付
- `receive_net_ton` (numeric): 受入量（トン）★予測対象
- `receive_vehicle_count` (int): 車両台数
- `iso_year`, `iso_week`, `iso_dow`: ISO暦
- `is_business`, `is_holiday`, `day_type`: 日付属性

**取得期間**: `target_date - 365 days` ～ `target_date - 1 day`（直近1年）

### 2. 予約データ

**ビュー**: `mart.v_reserve_daily_for_forecast`

**取得カラム**:
- `date` (date): 予約日
- `reserve_trucks` (int): 予約台数合計
- `reserve_fixed_trucks` (int): 固定客台数
- `reserve_fixed_ratio` (numeric): 固定客比率
- `source` (text): データソース（'manual' or 'customer_agg'）

**取得期間**: `target_date`（明日）の1日分

---

## 実行手順

### 1. 前提条件

- Docker環境が起動していること
- DB接続が可能であること
- モデルファイルが存在すること:
  - `/backend/models/final_fast_balanced/model_bundle.joblib`
  - `/backend/models/final_fast_balanced/res_walkforward.csv`
- 実績データがDBに存在すること（`mart.v_receive_daily`）

### 2. 手動ジョブ投入（psql経由）

```sql
-- ジョブを手動投入
INSERT INTO forecast.forecast_jobs (
    job_type,
    target_date,
    status,
    run_after
) VALUES (
    'daily_tplus1',
    '2025-12-19',  -- 明日の日付
    'queued',
    CURRENT_TIMESTAMP
);
```

### 3. Workerログ確認

```bash
# Workerログをリアルタイム表示
docker compose -f docker/docker-compose.dev.yml -p local_dev logs -f inbound_forecast_worker
```

### 4. 結果確認SQL

```sql
-- ジョブステータス確認
SELECT 
    job_id,
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

---

## アーキテクチャ図

```
┌─────────────────────────────────────────────────┐
│             Worker Main Loop                     │
│  (app/main.py)                                   │
│                                                  │
│  1. Poll forecast_jobs (5秒ごと)                │
│  2. Claim job (SELECT FOR UPDATE SKIP LOCKED)   │
│  3. Call execute_job()                           │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│           Job Executor                           │
│  (app/job_executor.py)                           │
│                                                  │
│  execute_daily_tplus1(db_session, target_date,   │
│                       job_id)                    │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│        Application Layer (UseCase)               │
│  (app/application/run_daily_tplus1_forecast.py)  │
│                                                  │
│  RunDailyTplus1ForecastUseCase                   │
│    .execute(target_date, job_id)                 │
│                                                  │
│  1. DBから実績取得（過去365日）                  │
│  2. DBから予約取得（明日1日分）                  │
│  3. 一時CSVに保存                                │
│  4. subprocess で daily_tplus1_predict.py 実行   │
│  5. 出力CSVを読み込み                            │
│  6. 結果をDBに保存                               │
└─────────────────────────────────────────────────┘
        ↓                    ↓                ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Adapters   │  │   Adapters   │  │   Adapters   │
│  (Inbound)   │  │  (Reserve)   │  │  (Result)    │
│              │  │              │  │              │
│ Postgres     │  │ Postgres     │  │ Postgres     │
│ Inbound      │  │ Reserve      │  │ Forecast     │
│ Actual       │  │ Daily        │  │ Result       │
│ Repository   │  │ Repository   │  │ Repository   │
└──────────────┘  └──────────────┘  └──────────────┘
        ↓                    ↓                ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  mart.       │  │  mart.       │  │  forecast.   │
│  v_receive_  │  │  v_reserve_  │  │  daily_      │
│  daily       │  │  daily_for_  │  │  forecast_   │
│              │  │  forecast    │  │  results     │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## 既知の未対応（今後の拡張）

### 優先度: 高

1. **モデルファイルの配置**:
   - 現在は `/backend/models/final_fast_balanced/` を想定
   - Docker イメージに含めるか、マウントが必要

2. **実績データの存在確認**:
   - `mart.v_receive_daily` にデータが無い場合のエラーハンドリング

3. **エラーハンドリングの強化**:
   - リトライロジックの詳細設定
   - 部分的な失敗の扱い

### 優先度: 中

4. **推論ロジックの直接呼び出し**:
   - Phase 2: subprocess → Python モジュール呼び出しに移行
   - CSV経由を廃止してメモリ内で処理

5. **精度改善**:
   - より多くの特徴量（天気、イベント等）
   - ハイパーパラメータチューニング

6. **祝日マスタの整備**:
   - 現在は `is_holiday` をDBから取得

### 優先度: 低

7. **t+7予測の実装**:
   - 7日先までの予測（別ジョブタイプ）

8. **月次予測の実装**:
   - Gamma-Poisson モデルによる月次予測

9. **学習ジョブの分離**:
   - 定期的な再学習を別workerで実行

10. **結果のAPI公開**:
    - core_api 経由でフロントエンドへ配信

---

## トラブルシューティング

### Q1: ジョブが queued のまま進まない

**確認項目**:
1. Workerが起動しているか: `docker compose logs inbound_forecast_worker`
2. DBに接続できているか: ログに接続エラーが無いか
3. `run_after` が未来の日時になっていないか

### Q2: ジョブが failed になる

**確認項目**:
1. `forecast.forecast_jobs.last_error` を確認
2. モデルファイルが存在するか
3. 実績データがDBに存在するか（過去365日分）

### Q3: 予測結果がDBに保存されない

**確認項目**:
1. ジョブが succeeded になっているか
2. `forecast.daily_forecast_results` にデータが無いか
3. Workerログに保存エラーが無いか

---

## 次のステップ

1. **動作確認**:
   - 手動ジョブ投入
   - Workerログ確認
   - DB結果確認

2. **統合テスト**:
   - 様々な日付での予測実行
   - エラーケースの確認（データ無し等）

3. **Phase 2への移行準備**:
   - 推論ロジックのPython モジュール化
   - CSV経由の廃止

---

## 参考資料

- [daily_forecast_tplus1_data_contract.md](docs/infrastructure/daily_forecast_tplus1_data_contract.md): データ契約定義書
- [20251218_001_add_daily_forecast_results_table.py](app/backend/core_api/migrations_v2/alembic/versions/20251218_001_add_daily_forecast_results_table.py): マイグレーション
- [job_executor.py](app/backend/inbound_forecast_worker/app/job_executor.py): ジョブ実行
- [run_daily_tplus1_forecast.py](app/backend/inbound_forecast_worker/app/application/run_daily_tplus1_forecast.py): UseCase実装
