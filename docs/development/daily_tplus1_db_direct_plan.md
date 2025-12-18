# CSV廃止→DB直結：日次t+1予測の実装計画書

## 📊 調査結果

### 1. DBスキーマ

#### 1.1 実績データソース（品目別）

**テーブル**: `stg.shogun_final_receive`

| カラム名（英語） | 型 | 説明 | 
|--------------|------|------|
| slip_date | date | 伝票日付 |
| item_name | text | 品名 |
| net_weight | numeric | 正味重量（kg） |
| is_deleted | boolean | 削除フラグ |

**現在のCSV列名（日本語）**:
- `伝票日付`: slip_date
- `品名`: item_name
- `正味重量`: net_weight / 1000.0 (kg→ton変換)

#### 1.2 予約データソース（日次集計）

**ビュー**: `mart.v_reserve_daily_for_forecast`

| カラム名（英語） | 型 | 説明 |
|--------------|------|------|
| date | date | 予約日 |
| reserve_trucks | bigint | 台数 |
| reserve_fixed_trucks | bigint | 固定客台数 |
| reserve_fixed_ratio | numeric | 固定客比率 |
| source | text | データソース |

**現在のCSV列名（日本語）**:
- `予約日`: date
- `台数`: reserve_trucks
- `固定客`: reserve_fixed_trucks

#### 1.3 実績データソース（日次集計）※利用可能だが現在未使用

**ビュー**: `mart.mv_receive_daily` (Materialized View)

| カラム名（英語） | 型 | 説明 |
|--------------|------|------|
| ddate | date | 日付 |
| receive_net_ton | numeric(18,3) | 正味重量合計（ton） |
| receive_vehicle_count | integer | 車両台数 |
| avg_weight_kg_per_vehicle | numeric(18,3) | 車両あたり平均重量（kg） |

**注**: train_daily_model.py は品目別データを要求するため、日次集計では不十分。stg.shogun_final_receive を継続使用する。

---

### 2. 学習スクリプトの引数要件

#### 2.1 train_daily_model.py (1258行)

**必須入力引数**:
```python
--raw-csv: str  # 実績CSV（必須ではないがデフォルト運用）
--raw-date-col: str = "伝票日付"  # 日付列名
--raw-item-col: str = "品名"  # 品目列名
--raw-weight-col: str = "正味重量"  # 重量列名（ton単位想定）

--reserve-csv: str (optional)  # 予約CSV
--reserve-date-col: str = "予約日"
--reserve-count-col: str = "台数"
--reserve-fixed-col: str = "固定客"

--out-dir: str (required)  # 出力ディレクトリ
--save-bundle: str (optional)  # モデル保存パス
```

**入力データ形式**:
- 実績CSV: 品目別日次データ（1行=1品目×1日）
  - 列: [伝票日付, 品名, 正味重量]
  - 正味重量: ton単位
- 予約CSV: 日次集計データ（1行=1日）
  - 列: [予約日, 台数, 固定客]

**内部処理**:
- pandas.read_csv() でロード
- 列名は日本語想定（引数で変更可能）
- Stage1: 品目別OOFモデル構築
- Stage2: 合計予測モデル構築

#### 2.2 serve_predict_model_v4_2_4.py (1440行)

**必須入力引数**:
```python
--bundle: str (required)  # train_daily_model.pyが保存したjoblibファイル
--reserve-csv: str (optional)  # 予測期間の予約データ
--reserve-date-col: str = "予約日"
--future-days: int (optional)  # 予測日数
--start-date: str (optional)  # 予測開始日
--end-date: str (optional)  # 予測終了日
--out-csv: str (required)  # 出力CSV
```

**出力形式**:
```csv
date, sum_items_pred, p50, p90, mean_pred, total_pred
2025-12-19, 79.5, 82.3, 95.1, 79.5, 79.5
```

**列の説明**:
- `date`: 予測日
- `p50`: Stage2モデルの中央値予測（主要指標）
- `p90`: Stage2モデルの90パーセンタイル予測
- `mean_pred`: Stage2モデルの平均予測
- `total_pred`: Stage1品目合計予測（参考）

---

### 3. 現在のアーキテクチャ（CSV方式）

**フロー**:
```
RunDailyTplus1ForecastWithTrainingUseCase
  ├─ 1. InboundActualsExporter.export_item_level_actuals()
  │     → stg.shogun_final_receive → raw.csv (品目別、365日)
  │
  ├─ 2. ReserveExporter.export_daily_reserve()
  │     → mart.v_reserve_daily_for_forecast → reserve.csv (67日)
  │
  ├─ 3. subprocess.run(retrain_and_eval.py)
  │     ├─ train_daily_model.py --raw-csv raw.csv --reserve-csv reserve.csv
  │     │   → out/bundle.joblib
  │     │
  │     └─ daily_tplus1_predict.py --bundle out/bundle.joblib
  │           → tplus1_pred.csv
  │
  └─ 4. pd.read_csv(tplus1_pred.csv) → p50取得 → DB保存
```

**問題点**:
- CSV中間ファイルの生成・読み込みオーバーヘッド
- ディスク容量消費
- 文字コードトラブル（UTF-8/Shift-JIS）
- デバッグ時のファイル管理コスト

---

### 4. 目標アーキテクチャ（DB直結方式）

**フロー**:
```
RunDailyTplus1ForecastWithTrainingUseCase
  ├─ 1. InboundActualsExporter.export_item_level_actuals()
  │     → stg.shogun_final_receive → pandas DataFrame (品目別、365日)
  │
  ├─ 2. ReserveExporter.export_daily_reserve()
  │     → mart.v_reserve_daily_for_forecast → pandas DataFrame (67日)
  │
  ├─ 3. subprocess.run(retrain_and_eval.py --use-db)
  │     ├─ train_daily_model.py --use-db
  │     │   ├─ load_raw_from_db() → DataFrame (内部でDB接続)
  │     │   ├─ load_reserve_from_db() → DataFrame
  │     │   └─ 既存処理（特徴量生成→学習→保存）
  │     │       → out/bundle.joblib
  │     │
  │     └─ daily_tplus1_predict.py --bundle --use-db
  │           ├─ load_reserve_from_db() → DataFrame
  │           └─ 予測 → tplus1_pred.csv (一時的に生成、またはJSON返却)
  │
  └─ 4. 予測結果をメモリ経由でDB保存（CSVは使わない）
```

**利点**:
- CSV I/Oの削除（速度向上）
- ディスク使用量削減
- 文字コードトラブル解消
- データ取得範囲の一元管理（UseCaseで統一）

---

## 🎯 実装方針：ベイビーステップ（既存コードを壊さない）

### 原則
1. **既存CLI引数は削除しない** → 追加のみ
2. **デフォルトは従来通り** → --use-db は明示的に指定
3. **特徴量生成ロジックは不変** → 入力DataFrame整形で対応
4. **段階的移行** → CSV方式と共存期間を設ける

### Phase 1: train_daily_model.py への --use-db 追加

**変更箇所**:
```python
# 引数追加
ap.add_argument("--use-db", action="store_true",
                help="DBから直接データ取得（CSVを使わない）")
ap.add_argument("--db-connection-string", type=str, default=None,
                help="PostgreSQL接続文字列（--use-db時に指定）")

# main()内で分岐
if args.use_db:
    # DBから直接取得
    raw_df = load_raw_from_db(
        connection_string=args.db_connection_string,
        start_date=...,  # ← 引数またはデフォルト計算
        end_date=...,
        date_col=args.raw_date_col,
        item_col=args.raw_item_col,
        weight_col=args.raw_weight_col,
    )
    
    if args.reserve_csv or args.use_db:
        reserve_df = load_reserve_from_db(
            connection_string=args.db_connection_string,
            start_date=...,
            end_date=...,
            date_col=args.reserve_date_col,
            count_col=args.reserve_count_col,
            fixed_col=args.reserve_fixed_col,
        )
else:
    # 従来通りCSVから読み込み
    raw_df = pd.read_csv(args.raw_csv, ...)
    if args.reserve_csv:
        reserve_df = pd.read_csv(args.reserve_csv, ...)
```

**新規関数**:
```python
def load_raw_from_db(
    connection_string: str,
    start_date: date,
    end_date: date,
    date_col: str,
    item_col: str,
    weight_col: str,
) -> pd.DataFrame:
    """
    stg.shogun_final_receive から品目別実績を取得
    
    Returns:
        DataFrame with columns: [date_col, item_col, weight_col]
        weight_col は ton 単位
    """
    import sqlalchemy
    from sqlalchemy import text
    
    engine = sqlalchemy.create_engine(connection_string)
    
    sql = text("""
        SELECT 
            slip_date AS date_col,
            item_name AS item_col,
            net_weight / 1000.0 AS weight_col
        FROM stg.shogun_final_receive
        WHERE slip_date >= :start_date 
          AND slip_date <= :end_date
          AND is_deleted = false
          AND net_weight IS NOT NULL
          AND item_name IS NOT NULL
        ORDER BY slip_date, item_name
    """)
    
    with engine.connect() as conn:
        result = conn.execute(sql, {
            "start_date": start_date,
            "end_date": end_date
        })
        rows = result.fetchall()
    
    df = pd.DataFrame(rows, columns=[date_col, item_col, weight_col])
    
    # 日付型変換
    df[date_col] = pd.to_datetime(df[date_col]).dt.normalize()
    
    return df


def load_reserve_from_db(
    connection_string: str,
    start_date: date,
    end_date: date,
    date_col: str,
    count_col: str,
    fixed_col: str,
) -> pd.DataFrame:
    """
    mart.v_reserve_daily_for_forecast から予約データを取得
    
    Returns:
        DataFrame with columns: [date_col, count_col, fixed_col]
    """
    import sqlalchemy
    from sqlalchemy import text
    
    engine = sqlalchemy.create_engine(connection_string)
    
    sql = text("""
        SELECT 
            date AS date_col,
            reserve_trucks AS count_col,
            reserve_fixed_trucks AS fixed_col
        FROM mart.v_reserve_daily_for_forecast
        WHERE date >= :start_date 
          AND date <= :end_date
        ORDER BY date
    """)
    
    with engine.connect() as conn:
        result = conn.execute(sql, {
            "start_date": start_date,
            "end_date": end_date
        })
        rows = result.fetchall()
    
    df = pd.DataFrame(rows, columns=[date_col, count_col, fixed_col])
    
    # 日付型変換
    df[date_col] = pd.to_datetime(df[date_col]).dt.normalize()
    
    return df
```

**注意**:
- 既存の `pd.read_csv()` の後続処理（日付パース、型変換等）をそのまま使えるようにDataFrameを整形
- 列名は引数で指定された日本語列名に合わせる
- ton単位への変換は取得時に実施（`/ 1000.0`）

---

### Phase 2: serve_predict_model_v4_2_4.py への --use-db 追加

**変更箇所**:
```python
# 引数追加
ap.add_argument("--use-db", action="store_true",
                help="DBから予約データを直接取得")
ap.add_argument("--db-connection-string", type=str, default=None,
                help="PostgreSQL接続文字列（--use-db時）")

# main()内で分岐
if args.use_db and args.db_connection_string:
    reserve_df = load_reserve_from_db(
        connection_string=args.db_connection_string,
        start_date=...,  # 予測開始日
        end_date=...,  # 予測終了日
        date_col=args.reserve_date_col,
        count_col=...,
        fixed_col=...,
    )
elif args.reserve_csv:
    reserve_df = pd.read_csv(args.reserve_csv, ...)
else:
    reserve_df = None
```

**注**:
- `load_reserve_from_db()` は train_daily_model.py と共通化（共通モジュールに抽出）

---

### Phase 3: retrain_and_eval.py / daily_tplus1_predict.py への引数転送

**retrain_and_eval.py**:
```python
# 引数追加
ap.add_argument("--use-db", action="store_true")
ap.add_argument("--db-connection-string", type=str, default=None)

# train_daily_model.py への転送
if args.use_db:
    cmd_train.extend([
        "--use-db",
        "--db-connection-string", args.db_connection_string,
    ])

# daily_tplus1_predict.py への転送
if args.use_db:
    cmd_pred.extend([
        "--use-db",
        "--db-connection-string", args.db_connection_string,
    ])
```

**daily_tplus1_predict.py**:
```python
# 引数追加
ap.add_argument("--use-db", action="store_true")
ap.add_argument("--db-connection-string", type=str, default=None)

# serve_predict_model_v4_2_4.py への転送
if args.use_db:
    cmd.extend([
        "--use-db",
        "--db-connection-string", args.db_connection_string,
    ])
```

---

### Phase 4: UseCase の変更（CSV廃止）

**RunDailyTplus1ForecastWithTrainingUseCase**:

**変更前**:
```python
# CSV保存
raw_csv_path = workspace / "raw.csv"
actuals_df.to_csv(raw_csv_path, index=False, encoding="utf-8")

reserve_csv_path = workspace / "reserve.csv"
reserve_df.to_csv(reserve_csv_path, index=False, encoding="utf-8")

# コマンド実行
cmd = [
    "python3", str(self._retrain_script_path),
    "--quick",
    "--raw-csv", str(raw_csv_path),
    "--reserve-csv", str(reserve_csv_path),
    ...
]
```

**変更後**:
```python
# CSV保存は不要（--use-dbモード）

# DB接続文字列を環境変数またはコンストラクタから取得
db_url = os.getenv("DATABASE_URL") or self._db_url

# コマンド実行
cmd = [
    "python3", str(self._retrain_script_path),
    "--quick",
    "--use-db",
    "--db-connection-string", db_url,
    "--start-date", str(target_date),
    "--end-date", str(target_date),
    "--out-dir", str(out_dir),
    "--pred-out-csv", str(pred_out_csv),
    ...
]
```

**日付範囲の統一**:
```python
# 実績データ範囲
actuals_start = target_date - timedelta(days=360)
actuals_end = target_date - timedelta(days=1)

# 予約データ範囲
reserve_start = target_date - timedelta(days=360)
reserve_end = target_date

# スクリプトに渡す（内部でDB取得時に使用）
cmd.extend([
    "--actuals-start-date", str(actuals_start),
    "--actuals-end-date", str(actuals_end),
    "--reserve-start-date", str(reserve_start),
    "--reserve-end-date", str(reserve_end),
])
```

**注意**:
- 現状では retrain_and_eval.py は日付範囲を受け取っていないため、追加実装が必要
- または、UseCase側でDataFrameをpickle化してスクリプトに渡す方式も検討（非推奨）

---

### Phase 5: 受入トン→数量変換（仕様確認必要）

**現状**:
- `正味重量` 列は ton 単位
- train_daily_model.py はこの値を直接使用
- 変換は不要？

**もし変換が必要な場合**:
```python
def ton_to_quantity(ton: float) -> float:
    """
    受入トン数を「数量」単位に変換
    
    仕様:
    - 1台あたり平均重量を基準に換算
    - または固定係数（例: 1 ton = 10 quantity）
    
    TODO: 正確な変換仕様を docs に記載
    """
    # 暫定実装
    CONVERSION_FACTOR = 1.0  # 1:1変換（仕様確認待ち）
    return ton * CONVERSION_FACTOR
```

**適用箇所**:
- `load_raw_from_db()` の返却DataFrame
- `正味重量` 列を変換後の値に置き換え

**ただし**:
- 学習側が ton 単位を想定しているなら変換不要
- 変換が必要かどうかは学習結果の単位と一致させる必要あり
- **結論**: 現状の実装では ton 単位のまま使用しており、変換は不要と判断

---

## 📝 実装チェックリスト

### Phase 1: スクリプト層への --use-db 追加
- [ ] `scripts/train_daily_model.py` に `load_raw_from_db()` 追加
- [ ] `scripts/train_daily_model.py` に `load_reserve_from_db()` 追加
- [ ] `scripts/train_daily_model.py` に `--use-db` 引数追加
- [ ] `scripts/serve_predict_model_v4_2_4.py` に `load_reserve_from_db()` 追加
- [ ] `scripts/serve_predict_model_v4_2_4.py` に `--use-db` 引数追加

### Phase 2: 共通化
- [ ] `scripts/db_utils.py` 作成（load_raw_from_db, load_reserve_from_db を共通化）
- [ ] train_daily_model.py, serve_predict_model_v4_2_4.py から import

### Phase 3: ラッパースクリプトへの引数転送
- [ ] `scripts/retrain_and_eval.py` に `--use-db` 追加・転送
- [ ] `scripts/daily_tplus1_predict.py` に `--use-db` 追加・転送

### Phase 4: UseCase層の変更
- [ ] `RunDailyTplus1ForecastWithTrainingUseCase` から CSV保存を削除
- [ ] `--use-db` フラグと DB接続文字列をコマンドに追加
- [ ] 日付範囲を引数として渡す（スクリプト側で受け取り）

### Phase 5: テストと監査
- [ ] デバッグモードで1ジョブ実行（--use-db あり）
- [ ] workspace確認（CSV生成されていないこと）
- [ ] DB保存確認（予測値が正常範囲）
- [ ] audit.md 作成（証拠付き検証）

---

## 🔍 検証項目（監査レポートに記載）

### 1. データ取得範囲の検証

**SQL実行例**:
```sql
-- 実績データ範囲
SELECT 
    MIN(slip_date) AS min_date,
    MAX(slip_date) AS max_date,
    COUNT(*) AS row_count,
    COUNT(DISTINCT item_name) AS item_count,
    AVG(net_weight / 1000.0) AS avg_weight_ton
FROM stg.shogun_final_receive
WHERE slip_date >= CURRENT_DATE - 360
  AND slip_date <= CURRENT_DATE - 1
  AND is_deleted = false
  AND net_weight IS NOT NULL
  AND item_name IS NOT NULL;

-- 予約データ範囲
SELECT 
    MIN(date) AS min_date,
    MAX(date) AS max_date,
    COUNT(*) AS row_count,
    AVG(reserve_trucks) AS avg_trucks
FROM mart.v_reserve_daily_for_forecast
WHERE date >= CURRENT_DATE - 360
  AND date <= CURRENT_DATE;
```

**期待値**:
- 実績: `[target_date - 360, target_date - 1]`
- 予約: `[target_date - 360, target_date]`

### 2. 列名変換の検証

**コード確認箇所**:
- `load_raw_from_db()` の返却DataFrame列名
- `load_reserve_from_db()` の返却DataFrame列名

**期待値**:
- 実績: `[伝票日付, 品名, 正味重量]`
- 予約: `[予約日, 台数, 固定客]`

### 3. 学習・予測の実行確認

**ログ確認**:
```bash
docker compose logs inbound_forecast_worker | grep -E "Starting|completed|p50="
```

**期待出力**:
```
Starting daily t+1 forecast with training
Training completed successfully
Prediction result: p50=75.3 ton
Saved prediction result to DB
```

### 4. DB保存の検証

**SQL実行例**:
```sql
SELECT 
    target_date,
    p50,
    p10,
    p90,
    unit,
    input_snapshot->>'model_version' AS model_version,
    input_snapshot->>'training_mode' AS training_mode,
    generated_at
FROM forecast.daily_forecast_results
WHERE target_date = CURRENT_DATE
ORDER BY generated_at DESC
LIMIT 1;
```

**期待値**:
- `p50` が 20～100 ton 範囲（異常値でない）
- `unit = 'ton'`
- `model_version = 'final_fast_balanced'`
- `training_mode = 'quick'`

### 5. CSV廃止の確認

**ワークスペース確認**:
```bash
ls -la /tmp/forecast_jobs/{job_id}/
# 期待: raw.csv, reserve.csv が存在しない
# 存在: out/, tplus1_pred.csv (一時的), run.log
```

**注**: tplus1_pred.csv は serve_predict_model_v4_2_4.py の出力として残る可能性あり（後続フェーズで削除検討）

---

## 🚀 実装優先順位

### P0（必須）
1. train_daily_model.py への --use-db 実装
2. serve_predict_model_v4_2_4.py への --use-db 実装
3. retrain_and_eval.py / daily_tplus1_predict.py への引数転送
4. UseCase からCSV保存削除・--use-db 指定

### P1（推奨）
5. db_utils.py への共通化
6. 日付範囲引数の明示化
7. 監査レポート作成

### P2（将来）
8. tplus1_pred.csv も廃止（JSON経由で結果を返す）
9. 環境変数での接続文字列管理（セキュリティ）
10. 統合テストの自動化

---

## ⚠️ リスクと対策

### リスク1: DB接続エラー
- **対策**: 接続文字列の検証、リトライ機構
- **フォールバック**: CSV方式に戻せるよう --use-db はオプション

### リスク2: 日付範囲のミスマッチ
- **対策**: UseCase で統一的に計算し、引数として渡す
- **検証**: 監査レポートで実際のSQL結果を確認

### リスク3: 既存コードの破壊
- **対策**: デフォルトは従来通り（--use-db は明示指定）
- **テスト**: CSV方式でも引き続き動作することを確認

### リスク4: パフォーマンス低下
- **対策**: DB側でインデックス確認（ddate, slip_date）
- **測定**: 実行時間をログに記録

---

## 📚 参考情報

### 既存実装
- `app/backend/inbound_forecast_worker/app/adapters/forecast/inbound_actuals_exporter.py` (品目別実績エクスポーター)
- `app/backend/inbound_forecast_worker/app/adapters/forecast/reserve_exporter.py` (予約エクスポーター)
- `app/backend/inbound_forecast_worker/app/application/run_daily_tplus1_forecast_with_training.py` (UseCase)

### スキーマ
- `data/postgres/` (ローカルDB)
- `docs/database/` (スキーマドキュメント)

### 学習スクリプト
- `app/backend/inbound_forecast_worker/scripts/train_daily_model.py` (学習)
- `app/backend/inbound_forecast_worker/scripts/serve_predict_model_v4_2_4.py` (推論)
- `app/backend/inbound_forecast_worker/scripts/retrain_and_eval.py` (ラッパー)

---

## ✅ 次のアクション

1. **Phase 1実装**: train_daily_model.py に --use-db を追加
2. **Phase 2実装**: serve_predict_model_v4_2_4.py に --use-db を追加
3. **Phase 3実装**: ラッパースクリプトへの引数転送
4. **Phase 4実装**: UseCase の変更（CSV廃止）
5. **Phase 5検証**: テスト実行と監査レポート作成

---

**作成日**: 2025-12-18  
**バージョン**: 1.0  
**ステータス**: 調査完了・実装待ち
