# DB→学習→t+1予測 E2E実装計画

**作成日**: 2025-12-18  
**目的**: forecast.forecast_jobs に daily_tplus1 ジョブを投入すると、DBからデータ取得→retrain_and_eval.py --quick で学習→結果DB保存まで自動実行する

---

## Step 0: 事前調査結果

### 1. DB構造確認

#### 実績データ: mart.v_receive_daily（日次合計のみ）

```sql
-- カラム構成
ddate                     | date          -- 日付
y, m                      | integer       -- 年月
iso_year, iso_week, iso_dow | integer     -- ISO週番号
is_business, is_holiday   | boolean       -- 営業日フラグ
day_type                  | text          -- 日付タイプ
receive_net_ton           | numeric(18,3) -- 受入正味重量（ton）
receive_vehicle_count     | integer       -- 台数
avg_weight_kg_per_vehicle | numeric(18,3) -- 車両あたり平均kg
sales_yen                 | numeric(18,0) -- 売上
unit_price_yen_per_kg     | numeric(18,3) -- kg単価
source_system             | text          -- データソース
```

**重要**: このビューは**日次合計のみ**で品目別データなし

#### 品目別受入データ: stg.shogun_final_receive（明細あり）

```sql
-- 主要カラム
slip_date         | date    -- 伝票日付
item_cd           | text    -- 品目コード
item_name         | text    -- 品名
net_weight        | numeric -- 正味重量（kg）
aggregate_item_cd | text    -- 集約品目コード
aggregate_item_name | text  -- 集約品目名
is_deleted        | boolean -- 削除フラグ
```

**判定**: retrain_and_eval.py が要求する「品目別形式」は stg.shogun_final_receive から取得可能

#### 予約データ: mart.v_reserve_daily_for_forecast

```sql
-- カラム構成
date                 | date    -- 日付
reserve_trucks       | bigint  -- 予約台数
reserve_fixed_trucks | bigint  -- 固定客予約台数
reserve_fixed_ratio  | numeric -- 固定客比率
source               | text    -- データソース
```

#### 結果保存先: forecast.daily_forecast_results（既存）

```sql
-- カラム構成
id            | uuid          -- PK
target_date   | date          -- 予測対象日（t+1）
job_id        | uuid          -- FK to forecast.forecast_jobs(id)
p50           | numeric(18,3) -- 中央値予測（メイン）
p10           | numeric(18,3) -- 10パーセンタイル（下側）
p90           | numeric(18,3) -- 90パーセンタイル（上側）
unit          | text          -- 単位（ton/kg）
generated_at  | timestamptz   -- 生成日時
input_snapshot| jsonb         -- 入力データ詳細

CONSTRAINT: UNIQUE (target_date, job_id)
```

**判定**: テーブル既存、マイグレーション不要（20251218_001で作成済み）

---

## Step 1: retrain_and_eval.py の引数拡張

### 追加する引数

```python
# 既存引数
--quick                    # クイックモード（既存）
--bootstrap-iters <int>    # イテレーション数（既存）
--n-jobs <int>             # 並列度（既存）
--log <path>               # ログパス（既存）

# 新規追加（パス制御）
--raw-csv <path>           # 学習入力CSV（品目別形式: 伝票日付,品名,正味重量）
--reserve-csv <path>       # 予約CSV（予約日,台数,固定客）
--out-dir <dir>            # 出力ディレクトリ（bundle/res_walkforward出力先）
--pred-out-csv <path>      # t+1予測結果CSV出力先
--start-date <YYYY-MM-DD>  # 予測基準日（省略時は最新データ日の翌日）
```

### 既存の固定パス（デフォルト維持）

```python
# 引数未指定時のデフォルト
detail_csv_path = f"{DATA_DIR}/input/20240501-20250422.csv"       # 優先
raw_csv_path = f"{DATA_DIR}/input/01_daily_clean.csv"             # 次点（合計→ダミー変換）
dummy_csv_path = f"{DATA_DIR}/input/01_daily_clean_dummy_item.csv"
reserve_csv = f"{DATA_DIR}/input/yoyaku_data.csv"
OUT_DIR = f"{DATA_DIR}/output/final_fast_balanced"
```

### 変更方針

1. `argparse` に新規引数を追加
2. 引数指定時はそれを優先、未指定時は既存パスを使用（後方互換性維持）
3. `cmd_train` / `cmd_pred` の構築時に引数ベースのパスを使用

---

## Step 2: DB→CSV エクスポート機能（Ports & Adapters）

### 2-1. 生成するCSV仕様

#### raw.csv（学習用、日本語ヘッダ）

```csv
伝票日付,品名,正味重量
2024-12-18,混合廃棄物,1.234
2024-12-18,木くず,0.567
2024-12-19,混合廃棄物,2.345
```

- 伝票日付: YYYY-MM-DD形式
- 品名: item_name（文字列）
- 正味重量: ton単位（kg→ton変換必須）

#### reserve.csv（予約用、日本語ヘッダ）

```csv
予約日,台数,固定客
2024-12-18,45,30
2024-12-19,50,35
```

- 予約日: YYYY-MM-DD形式
- 台数: reserve_trucks（整数）
- 固定客: reserve_fixed_trucks（整数）

### 2-2. Repository構成（Ports & Adapters）

#### Port（抽象インターフェース）

```python
# app/core/ports/inbound_actuals_export_port.py
class InboundActualsExportPort(ABC):
    @abstractmethod
    def export_item_level_actuals(
        self,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        品目別日次実績を取得
        
        Returns:
            DataFrame with columns: [伝票日付, 品名, 正味重量]
            正味重量はton単位
        """
        pass

# app/core/ports/reserve_export_port.py
class ReserveExportPort(ABC):
    @abstractmethod
    def export_daily_reserve(
        self,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        日次予約データを取得
        
        Returns:
            DataFrame with columns: [予約日, 台数, 固定客]
        """
        pass
```

#### Adapter（実装）

```python
# app/infra/adapters/forecast/inbound_actuals_exporter.py
class InboundActualsExporter(InboundActualsExportPort):
    def export_item_level_actuals(self, start_date, end_date):
        sql = text("""
            SELECT 
                slip_date AS "伝票日付",
                item_name AS "品名",
                net_weight / 1000.0 AS "正味重量"  -- kg → ton
            FROM stg.shogun_final_receive
            WHERE slip_date >= :start_date 
              AND slip_date <= :end_date
              AND is_deleted = false
              AND net_weight IS NOT NULL
            ORDER BY slip_date, item_name
        """)
        result = self.db.execute(sql, {"start_date": start_date, "end_date": end_date})
        return pd.DataFrame(result.fetchall(), columns=["伝票日付", "品名", "正味重量"])

# app/infra/adapters/forecast/reserve_exporter.py
class ReserveExporter(ReserveExportPort):
    def export_daily_reserve(self, start_date, end_date):
        sql = text("""
            SELECT 
                date AS "予約日",
                reserve_trucks AS "台数",
                reserve_fixed_trucks AS "固定客"
            FROM mart.v_reserve_daily_for_forecast
            WHERE date >= :start_date 
              AND date <= :end_date
            ORDER BY date
        """)
        result = self.db.execute(sql, {"start_date": start_date, "end_date": end_date})
        return pd.DataFrame(result.fetchall(), columns=["予約日", "台数", "固定客"])
```

### 2-3. 取得期間の決定

```python
target_date = date.today() + timedelta(days=1)  # t+1

# 実績: 過去365日（1年分）
actuals_start = target_date - timedelta(days=365)
actuals_end = target_date - timedelta(days=1)  # 昨日まで

# 予約: 過去60日 + 未来7日
reserve_start = target_date - timedelta(days=60)
reserve_end = target_date + timedelta(days=7)
```

---

## Step 3: workspace方式でジョブ実行

### 3-1. workspace構造

```
/tmp/forecast_jobs/{job_id}/
  ├── raw.csv              # 品目別実績（日本語ヘッダ）
  ├── reserve.csv          # 予約データ（日本語ヘッダ）
  ├── out/
  │   ├── model_bundle.joblib       # 学習済みモデル
  │   └── res_walkforward.csv       # Walk-forward評価結果
  ├── tplus1_pred.csv      # t+1予測結果（最終出力）
  └── run.log              # 実行ログ
```

### 3-2. ジョブ実行フロー

```python
# app/core/usecases/forecast/run_daily_tplus1_forecast_usecase.py

class RunDailyTplus1ForecastUseCase:
    def execute(self, job_id: UUID, target_date: date):
        # 1. workspace作成
        ws = f"/tmp/forecast_jobs/{job_id}"
        os.makedirs(f"{ws}/out", exist_ok=True)
        
        # 2. DB→CSV生成
        actuals_df = actuals_port.export_item_level_actuals(
            start_date=target_date - timedelta(days=365),
            end_date=target_date - timedelta(days=1)
        )
        actuals_df.to_csv(f"{ws}/raw.csv", index=False)
        
        reserve_df = reserve_port.export_daily_reserve(
            start_date=target_date - timedelta(days=60),
            end_date=target_date + timedelta(days=7)
        )
        reserve_df.to_csv(f"{ws}/reserve.csv", index=False)
        
        # 3. retrain_and_eval.py実行
        cmd = [
            "python3", "/backend/scripts/retrain_and_eval.py",
            "--quick",
            "--raw-csv", f"{ws}/raw.csv",
            "--reserve-csv", f"{ws}/reserve.csv",
            "--out-dir", f"{ws}/out",
            "--pred-out-csv", f"{ws}/tplus1_pred.csv",
            "--start-date", str(target_date),
            "--log", f"{ws}/run.log",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        
        # 4. 結果読み取り→DB保存
        pred_df = pd.read_csv(f"{ws}/tplus1_pred.csv")
        forecast_result_repo.save_result(
            target_date=target_date,
            job_id=job_id,
            p50=pred_df["p50"].iloc[0],
            p10=pred_df.get("p10", [None]).iloc[0],
            p90=pred_df.get("p90", [None]).iloc[0],
            unit="ton",
            input_snapshot={
                "actuals_max_date": str(actuals_end),
                "actuals_count": len(actuals_df),
                "reserve_exists": len(reserve_df) > 0,
                "model_version": "final_fast_balanced",
            }
        )
        
        # 5. ジョブステータス更新
        job_repo.update_job_status(job_id, status="succeeded")
```

---

## Step 4: エラーハンドリング

### エラーシナリオと対応

| エラー | 検出方法 | 対応 |
|--------|---------|------|
| DB取得失敗 | SQLException | job status → failed, last_error に SQL/例外要約 |
| CSV生成失敗 | DataFrame.to_csv exception | job status → failed, last_error に詳細 |
| retrain_and_eval rc!=0 | subprocess returncode check | job status → failed, run.log末尾をlast_errorに要約 |
| 予測CSV不在/不正 | FileNotFoundError / pd.read_csv exception | job status → failed, last_error に詳細 |
| DB保存失敗 | SQLException | job status → failed, last_error に詳細 |

### 実装例

```python
try:
    # ... DB取得・CSV生成・学習実行 ...
    
    if result.returncode != 0:
        with open(f"{ws}/run.log", "r") as f:
            log_tail = f.readlines()[-50:]  # 末尾50行
        raise RuntimeError(f"retrain_and_eval failed: {''.join(log_tail)}")
    
    if not os.path.exists(f"{ws}/tplus1_pred.csv"):
        raise FileNotFoundError("Prediction output not found")
    
    # ... DB保存 ...
    
except Exception as e:
    job_repo.update_job_status(
        job_id=job_id,
        status="failed",
        last_error=str(e)[:500]  # 500文字まで
    )
    logger.error(f"Job {job_id} failed: {e}", exc_info=True)
    # worker は継続（次のジョブを処理）
```

---

## Step 5: E2E動作確認手順

### 5-1. ジョブ投入（SQL）

```sql
-- daily_tplus1 ジョブを投入
INSERT INTO forecast.forecast_jobs (
    id,
    job_type,
    target_date,
    status,
    priority,
    created_at
) VALUES (
    gen_random_uuid(),
    'daily_tplus1',
    CURRENT_DATE + 1,  -- 明日
    'pending',
    10,
    CURRENT_TIMESTAMP
);
```

### 5-2. Workerログ確認

```bash
# worker起動
cd /home/koujiro/work_env/22.Work_React/sanbou_app
docker compose -f docker/docker-compose.dev.yml -p local_dev logs -f inbound_forecast_worker

# 期待されるログ
# [INFO] Polling for pending jobs...
# [INFO] Picked up job: <job_id>, type=daily_tplus1
# [INFO] Exporting actuals from stg.shogun_final_receive...
# [INFO] Exported 12345 rows to /tmp/forecast_jobs/<job_id>/raw.csv
# [INFO] Exporting reserve from mart.v_reserve_daily_for_forecast...
# [INFO] Exported 67 rows to /tmp/forecast_jobs/<job_id>/reserve.csv
# [INFO] Running: python3 /backend/scripts/retrain_and_eval.py --quick ...
# [INFO] retrain_and_eval completed in 18m10s
# [INFO] Saving prediction to forecast.daily_forecast_results...
# [INFO] Job <job_id> succeeded
```

### 5-3. DB確認

```sql
-- ジョブステータス確認
SELECT 
    id,
    job_type,
    target_date,
    status,
    started_at,
    completed_at,
    last_error
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
WHERE target_date = CURRENT_DATE + 1
ORDER BY generated_at DESC
LIMIT 1;
```

### 5-4. workspace確認（コンテナ内）

```bash
# コンテナに入る
docker compose -f docker/docker-compose.dev.yml -p local_dev exec inbound_forecast_worker bash

# workspace確認
JOB_ID=<uuid>  # 上記SQLで取得
ls -lh /tmp/forecast_jobs/$JOB_ID/
# 期待: raw.csv, reserve.csv, out/, tplus1_pred.csv, run.log

# CSVサンプル確認
head -5 /tmp/forecast_jobs/$JOB_ID/raw.csv
head -5 /tmp/forecast_jobs/$JOB_ID/reserve.csv
cat /tmp/forecast_jobs/$JOB_ID/tplus1_pred.csv
```

---

## 既知の課題と対応方針

### 1. 処理時間

- **--quick モード**: 約18分（README記載）
- **フル学習**: 数時間
- **対応**: 初期実装は --quick のみ、本番運用時にフル学習を検討

### 2. データ量

- **365日分の品目別データ**: 数万〜数十万行想定
- **対応**: SQLで必要期間のみ取得、インデックス活用

### 3. workspace のクリーンアップ

- **問題**: /tmp配下にジョブごとのディレクトリが蓄積
- **対応**: 
  - 成功ジョブ: 7日後に自動削除
  - 失敗ジョブ: 30日後に自動削除（デバッグ用に保持）

### 4. 同時実行制御

- **問題**: 複数ジョブが同時実行されるとリソース圧迫
- **対応**: 
  - daily_tplus1 は1つずつ実行（同時実行数=1）
  - job_executorでロック機構を実装

### 5. Prod運用方針

- **Dev**: --quick で動作確認
- **Stg**: --quick で精度確認、失敗時の挙動検証
- **Prod**: 
  - 初期: --quick で運用開始
  - 安定後: フル学習に移行（週次バッチで学習、日次で推論のみ）

---

## 提出物チェックリスト

- [x] Step 0: DB構造調査（本ドキュメント）
- [ ] Step 1: retrain_and_eval.py の引数追加実装
- [ ] Step 2: Ports/Adapters 実装（Repository追加）
- [ ] Step 3: UseCase実装（workspace方式）
- [ ] Step 4: エラーハンドリング実装
- [ ] Step 5: E2E動作確認（ログ・DB・workspace）
- [ ] 最終ドキュメント作成（実行手順・サンプル・課題）

---

**次のアクション**: Step 1 retrain_and_eval.py の引数追加実装
