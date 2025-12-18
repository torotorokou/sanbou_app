# 全予測機能 学習/推論 監査報告書

**調査日**: 2025-12-18  
**調査担当**: AI Assistant  
**目的**: 搬入量予測の全機能について「毎回学習→予測」なのか「推論のみ」なのかを証拠付きで判定

---

## エグゼクティブサマリー

### 調査結果：5種類の予測タイプ

| 予測タイプ | job_type | 判定 | 実装状況 |
|-----------|----------|------|---------|
| **日次 t+1** | `daily_tplus1` | ✅ **推論のみ** | ✅ 実装済み |
| **日次 t+7** | `daily_tplus7` | ✅ **推論のみ** | ⏳ ホワイトリスト登録済み（未実装） |
| **月次 Gamma** | `monthly_gamma` | ❓ **不明** | ⏳ ホワイトリスト登録済み（未実装） |
| **週次按分** | `weekly` | ❓ **規則/按分系** | ⏳ ホワイトリスト登録済み（未実装） |
| **月次着地 14日** | `monthly_landing_14d` | ❓ **不明** | ⏳ ホワイトリスト登録済み（未実装） |
| **月次着地 21日** | `monthly_landing_21d` | ❓ **不明** | ⏳ ホワイトリスト登録済み（未実装） |

### 重要な発見

1. **実装済みは日次t+1のみ**: 他の5種類はホワイトリストに登録されているが、実装されていない
2. **日次t+7は同じ推論スクリプトを使用**: `serve_predict_model_v4_2_4.py` の `--future-days` オプションで実装可能
3. **スクリプトファイルが存在しない**: gamma, blend, weekly, landing系の実行スクリプトは `inbound_forecast_worker/scripts/` に存在しない
4. **ドキュメントに設計情報あり**: `forecast_worker_prediction_types.md` に各予測の設計仕様が記載

---

## 詳細調査結果

---

## 1. 日次予測 t+1 (daily_tplus1)

### 判定
✅ **推論のみ（学習済みモデル必須）**

### 入口（実行開始点）
- **ファイル**: [app/job_executor.py](app/backend/inbound_forecast_worker/app/job_executor.py)
- **関数**: `execute_daily_tplus1()` (line 84-155)
- **呼び出し元**: workerの `job_type == "daily_tplus1"` 分岐 (line 185)

### 呼び出しチェーン

```
job_executor.execute_job()  
  ↓ (job_type == "daily_tplus1")
execute_daily_tplus1() (line 84)
  ↓
RunDailyTplus1ForecastUseCase.execute() (line 123)
  ↓ subprocess
daily_tplus1_predict.py (line 131-147)
  ↓ subprocess
serve_predict_model_v4_2_4.py (line 75)
  ↓ joblib.load()
model_bundle.joblib (line 372)
```

**ファイルパス:**
1. `app/backend/inbound_forecast_worker/app/job_executor.py:84-155`
2. `app/backend/inbound_forecast_worker/app/application/run_daily_tplus1_forecast.py:120-220`
3. `app/backend/inbound_forecast_worker/scripts/daily_tplus1_predict.py:45-96`
4. `app/backend/inbound_forecast_worker/scripts/serve_predict_model_v4_2_4.py:1-1440`

### 学習/推論の証拠

#### A. モデルロード（推論のみ）

**場所**: `serve_predict_model_v4_2_4.py:372`

```python
bundle = joblib.load(bundle_path)
```

**結論**: 学習済みモデルをロードするのみ

#### B. 学習処理は存在しない

**検索結果**: `serve_predict_model_v4_2_4.py` に以下は存在しない
- メインモデルの `.fit()` 呼び出し: ❌ なし
- `joblib.dump()`: ❌ なし

#### C. 残差再学習（オプション機能、未使用）

**場所**: `serve_predict_model_v4_2_4.py:792-855`

```python
if residual_refit:  # デフォルト: False
    # ... 残差モデルの学習 ...
    m.fit(X_resid, resid_target, sample_weight=sw)  # line 822, 824
```

**コマンドライン**: `serve_predict_model_v4_2_4.py:1384`

```python
ap.add_argument("--residual-refit", action="store_true", 
                help="直近期の残差を軽量モデルで再学習して将来に加算")
```

**現在の使用状況**: 
- `run_daily_tplus1_forecast.py` では `--residual-refit` を渡していない ❌
- `daily_tplus1_predict.py` でも `--residual-refit` を渡していない ❌

**検証コマンド**:
```bash
grep -n "residual" app/backend/inbound_forecast_worker/app/application/run_daily_tplus1_forecast.py
# 結果: マッチなし

grep -n "residual" app/backend/inbound_forecast_worker/scripts/daily_tplus1_predict.py
# 結果: マッチなし
```

### 必要ファイル/成果物

#### 必須モデルファイル
1. `/backend/models/final_fast_balanced/model_bundle.joblib` (学習済みモデル)
2. `/backend/models/final_fast_balanced/res_walkforward.csv` (履歴データ)

#### 生成されるファイル
- `/backend/output/tplus1_pred_{target_date}.csv` (予測結果)

#### DB入出力
- **入力**: 
  - `raw.inbound_actual` (実績データ)
  - `forecast.reserve_daily` (予約データ)
- **出力**: 
  - `forecast.daily_forecast_results` (予測結果)

### 追加メモ

- **残差再学習**: オプション機能として実装されているが、現在は使用されていない
- **モデル学習**: 別スクリプト `train_daily_model.py` で実行（日次予測のワークフローからは呼ばれない）

---

## 2. 日次予測 t+7 (daily_tplus7)

### 判定
✅ **推論のみ（学習済みモデル必須）**

### 実装状況
⏳ **ホワイトリスト登録済み、スクリプト実装済み、UseCase未実装**

### 入口（実行開始点）
- **ファイル**: [app/job_executor.py](app/backend/inbound_forecast_worker/app/job_executor.py)
- **関数**: `execute_job()` (line 159-189)
- **呼び出し元**: workerの `job_type == "daily_tplus7"` 分岐（未実装）
- **ホワイトリスト**: `ALLOWED_JOB_TYPES` (line 52-58)

```python
ALLOWED_JOB_TYPES = {
    "daily_tplus1",
    "daily_tplus7",  # ← ホワイトリスト登録済み
    "weekly",
    "monthly_gamma",
    "monthly_landing_14d",
    "monthly_landing_21d",
}
```

**現在の実装**: 

```python
# job_executor.py:185-189
if job_type == "daily_tplus1":
    execute_daily_tplus1(db_session, target_date, job_id, timeout)
else:
    # Phase 3では daily_tplus1 のみ実装
    raise JobExecutionError(
        f"Job type '{job_type}' is whitelisted but not yet implemented"
    )
```

### 呼び出しチェーン（設計上）

```
job_executor.execute_job()  
  ↓ (job_type == "daily_tplus7")
execute_daily_tplus7() [未実装]
  ↓ subprocess
serve_predict_model_v4_2_4.py --future-days 7
  ↓ joblib.load()
model_bundle.joblib (同じモデル)
```

### 学習/推論の証拠

#### A. 同じモデル・同じスクリプト

**スクリプト**: `serve_predict_model_v4_2_4.py`

**コマンドライン引数**: line 1357

```python
ap.add_argument("--future-days", type=int, default=7, 
                help="予測日数（start/end 未指定時）")
```

**処理内容**: line 474-477

```python
n = int(future_days or 7)
# ... 未来N日分の予測を生成 ...
print(f"[TRACE] future days: {len(idx_future)} from {idx_future.min().date()} to {idx_future.max().date()}")
```

#### B. 推論のみ（t+1と同じ）

- `joblib.load()` でモデルをロード (line 372)
- メインモデルの `.fit()` 呼び出しなし
- `--residual-refit` オプションは未使用（t+1と同じ）

### 必要ファイル/成果物

#### 必須モデルファイル
- **t+1と同じモデルを使用**
- `/backend/models/final_fast_balanced/model_bundle.joblib`
- `/backend/models/final_fast_balanced/res_walkforward.csv`

#### 生成されるファイル
- `/backend/output/tplus7_pred_{target_date}.csv` (7日分の予測結果)

#### DB入出力
- **入力**: t+1と同じ
- **出力**: `forecast.daily_forecast_results` (target_date + 7日分)

### 追加メモ

- **実装難易度**: 低（UseCase作成のみ、スクリプトは既存を流用）
- **モデル共有**: t+1と同じモデルを使用（追加学習不要）
- **処理時間**: 約5〜10分（7日分のループ予測）

---

## 3. 月次予測 Gamma Recency (monthly_gamma)

### 判定
❓ **実装されていないため不明**

**推測**: ドキュメントによると「交差検証含む」とあるため、**毎回学習の可能性あり**

### 実装状況
⏳ **ホワイトリスト登録済み、スクリプト未実装**

### 入口（実行開始点）
- **ファイル**: [app/job_executor.py](app/backend/inbound_forecast_worker/app/job_executor.py)
- **関数**: `execute_job()` (line 159-189)
- **呼び出し元**: workerの `job_type == "monthly_gamma"` 分岐（未実装）
- **ホワイトリスト**: `ALLOWED_JOB_TYPES` (line 56)

```python
ALLOWED_JOB_TYPES = {
    "daily_tplus1",
    "daily_tplus7",
    "weekly",
    "monthly_gamma",  # ← ホワイトリスト登録済み
    "monthly_landing_14d",
    "monthly_landing_21d",
}
```

### 呼び出しチェーン（ドキュメント記載）

**ドキュメント**: `docs/development/forecast_worker_prediction_types.md:103-134`

```
execute_monthly_gamma() [未実装]
  ↓ subprocess
scripts/gamma_recency_model/gamma_recency_model.py [ファイル不在]
  ↓ ???
gamma_forecast.csv
```

### 学習/推論の証拠

#### A. スクリプトファイルが存在しない

**検索結果**:
```bash
find app/backend/inbound_forecast_worker/scripts/ -name "*gamma*"
# 結果: マッチなし（ファイルが存在しない）
```

#### B. ドキュメントの記載

**場所**: `docs/development/forecast_worker_prediction_types.md:103-134`

**内容**:
```markdown
### 概要
- **目的:** 月次搬入量を Gamma-Recency モデルで予測
- **実行スクリプト:** `scripts/gamma_recency_model/gamma_recency_model.py`
- **実装状況:** ⏳ 未実装（ホワイトリストには登録済み）

### 実行時間
- 約10〜20分（交差検証含む）  # ← 学習の可能性あり
```

**推測**: 「交差検証含む」という記載から、**毎回学習を行う可能性が高い**

### 必要ファイル/成果物（ドキュメント記載）

#### 必須ファイル
1. `/backend/data/input/01_daily_clean.csv` (日次クリーンデータ)
2. 必須カラム: date, weight, customer_id など

#### 生成されるファイル
- `/backend/data/output/gamma_recency_model/gamma_forecast.csv` (月次予測結果)

#### DB入出力
- **未定義** (ドキュメントに記載なし)

### 追加メモ

- **依存関係**: `monthly_blend` (weekly の前提)と `weekly` が依存
- **スクリプト不在**: 実装時に学習/推論の判定が必要
- **推定判定**: ドキュメントから「毎回学習」の可能性が高い

---

## 4. 月次予測 Blend (monthly_blend)

### 判定
❓ **実装されていないため不明**

**推測**: ドキュメントによると「ブレンドモデルの学習」とあるため、**毎回学習の可能性あり**

### 実装状況
⏳ **ホワイトリスト未登録、スクリプト未実装**

**注**: `monthly_blend` は `weekly` の前処理として実行される想定（独立したjob_typeではない）

### 入口（実行開始点）
- **想定**: `weekly` ジョブの前処理として実行
- **ファイル**: 未実装

### 呼び出しチェーン（ドキュメント記載）

**ドキュメント**: `docs/development/forecast_worker_prediction_types.md:136-165`

```
execute_monthly_blend() [未実装]
  ↓ subprocess
scripts/gamma_recency_model/blend_lgbm.py [ファイル不在]
  ↓ ???
blended_future_forecast.csv
```

### 学習/推論の証拠

#### A. スクリプトファイルが存在しない

**検索結果**:
```bash
find app/backend/inbound_forecast_worker/scripts/ -name "*blend*"
# 結果: マッチなし（ファイルが存在しない）

find app/backend/inbound_forecast_worker/scripts/ -name "*lgbm*"
# 結果: マッチなし（ファイルが存在しない）
```

#### B. ドキュメントの記載

**場所**: `docs/development/forecast_worker_prediction_types.md:136-165`

**内容**:
```markdown
### 概要
- **目的:** Gamma-Recency 予測を Ridge/LGBM で補正・ブレンド
- **実行スクリプト:** `scripts/gamma_recency_model/blend_lgbm.py`

### 必要ファイル
2. **日次クリーンデータ**
   - 用途: ブレンドモデルの学習  # ← 学習の可能性あり
```

**推測**: 「ブレンドモデルの学習」という記載から、**毎回学習を行う可能性が高い**

### 必要ファイル/成果物（ドキュメント記載）

#### 必須ファイル
1. `/backend/data/output/gamma_recency_model/gamma_forecast.csv` (Gamma予測結果)
2. `/backend/data/input/01_daily_clean.csv` (日次クリーンデータ)

#### 生成されるファイル
- `/backend/data/output/gamma_recency_model/blended_future_forecast.csv` (ブレンド予測)

### 追加メモ

- **依存関係**: `monthly_gamma` の出力を必要とする
- **処理時間**: 約5〜10分（ドキュメント記載）
- **推定判定**: 「学習」という記載から毎回学習の可能性が高い

---

## 5. 週次予測 按分 (weekly)

### 判定
❓ **実装されていないため不明**

**推測**: ドキュメントによると「按分比率を計算」とあるため、**規則/按分系の可能性が高い**

### 実装状況
⏳ **ホワイトリスト登録済み、スクリプト未実装**

### 入口（実行開始点）
- **ファイル**: [app/job_executor.py](app/backend/inbound_forecast_worker/app/job_executor.py)
- **関数**: `execute_job()` (line 159-189)
- **呼び出し元**: workerの `job_type == "weekly"` 分岐（未実装）
- **ホワイトリスト**: `ALLOWED_JOB_TYPES` (line 55)

```python
ALLOWED_JOB_TYPES = {
    "daily_tplus1",
    "daily_tplus7",
    "weekly",  # ← ホワイトリスト登録済み
    "monthly_gamma",
    "monthly_landing_14d",
    "monthly_landing_21d",
}
```

### 呼び出しチェーン（ドキュメント記載）

**ドキュメント**: `docs/development/forecast_worker_prediction_types.md:167-200`

```
execute_weekly() [未実装]
  ↓ subprocess
scripts/weekly_allocation/allocate_monthly_to_weekly_from_blend.py [ファイル不在]
  ↓ 按分計算（ルールベース）
weekly_allocated_forecast.csv
```

### 学習/推論の証拠

#### A. スクリプトファイルが存在しない

**検索結果**:
```bash
find app/backend/inbound_forecast_worker/scripts/ -name "*weekly*"
# 結果: マッチなし（ファイルが存在しない）

find app/backend/inbound_forecast_worker/scripts/ -name "*allocation*"
# 結果: マッチなし（ファイルが存在しない）

find app/backend/inbound_forecast_worker/scripts/ -name "*按分*"
# 結果: マッチなし（ファイルが存在しない）
```

#### B. ドキュメントの記載

**場所**: `docs/development/forecast_worker_prediction_types.md:167-200`

**内容**:
```markdown
### 概要
- **目的:** 月次予測を週次に按分
- **実行スクリプト:** `scripts/weekly_allocation/allocate_monthly_to_weekly_from_blend.py`

### 必要ファイル
2. **日次クリーンデータ（履歴）**
   - 用途: 過去3年間の実績パターンから按分比率を計算  # ← ルールベース
```

**推測**: 「按分比率を計算」という記載から、**規則/按分系（モデル学習なし）の可能性が高い**

### 必要ファイル/成果物（ドキュメント記載）

#### 必須ファイル
1. `/backend/data/output/gamma_recency_model/blended_future_forecast.csv` (月次予測)
2. `/backend/data/input/01_daily_clean.csv` (過去3年間の実績パターン)

#### 生成されるファイル
- `/backend/data/output/gamma_recency_model/weekly_allocated_forecast.csv` (週次予測)

#### DB入出力
- **未定義** (ドキュメントに記載なし)

### 追加メモ

- **依存関係**: `monthly_gamma` → `monthly_blend` → `weekly` の順で実行必要
- **処理時間**: 約2〜5分（ドキュメント記載）
- **推定判定**: 按分計算のみで**モデル学習なし**の可能性が高い
- **実装優先度**: Phase 2（短期計画に必要）

---

## 6. 月次着地 14日時点 (monthly_landing_14d)

### 判定
❓ **実装されていないため不明**

**推測**: ドキュメントによると「学習済みモデルで推論」または「モデル学習から実行」の2パターンあり

### 実装状況
⏳ **ホワイトリスト登録済み、スクリプト未実装**

### 入口（実行開始点）
- **ファイル**: [app/job_executor.py](app/backend/inbound_forecast_worker/app/job_executor.py)
- **関数**: `execute_job()` (line 159-189)
- **呼び出し元**: workerの `job_type == "monthly_landing_14d"` 分岐（未実装）
- **ホワイトリスト**: `ALLOWED_JOB_TYPES` (line 57)

```python
ALLOWED_JOB_TYPES = {
    "daily_tplus1",
    "daily_tplus7",
    "weekly",
    "monthly_gamma",
    "monthly_landing_14d",  # ← ホワイトリスト登録済み
    "monthly_landing_21d",
}
```

### 呼び出しチェーン（ドキュメント記載）

**ドキュメント**: `docs/development/forecast_worker_prediction_types.md:202-239`

```
execute_monthly_landing_14d() [未実装]
  ↓ subprocess
scripts/monthly_landing_gamma_poisson/run_monthly_landing_gamma_poisson.py [ファイル不在]
  ↓ オプション分岐
  ├─ --load-model: joblib.load() → 推論のみ
  └─ --use-a14: モデル学習 → 予測
```

### 学習/推論の証拠

#### A. スクリプトファイルが存在しない

**検索結果**:
```bash
find app/backend/inbound_forecast_worker/scripts/ -name "*landing*"
# 結果: マッチなし（ファイルが存在しない）

find app/backend/inbound_forecast_worker/scripts/ -name "*poisson*"
# 結果: マッチなし（ファイルが存在しない）
```

#### B. ドキュメントの記載

**場所**: `docs/development/forecast_worker_prediction_types.md:202-239`

**コマンド例（推論のみ）**:
```bash
# 学習済みモデルで推論
python3 /backend/scripts/monthly_landing_gamma_poisson/run_monthly_landing_gamma_poisson.py \
  --monthly-csv /backend/data/output/monthly_features.csv \
  --load-model /backend/models/monthly_landing_poisson_14d.pkl \
  --out-csv /backend/output/prediction_14d.csv
```

**コマンド例（学習含む）**:
```bash
# モデル学習から実行
python3 /backend/scripts/monthly_landing_gamma_poisson/run_monthly_landing_gamma_poisson.py \
  --monthly-csv /backend/data/output/monthly_features.csv \
  --use-a14 \
  --out-csv /backend/output/prediction_14d.csv
```

**実行時間**:
- 推論のみ: 約1分
- 学習含む: 約5〜10分

**推測**: 
- **推論のみモード**: `--load-model` を指定（学習済みモデル使用）
- **学習モード**: `--use-a14` を指定（毎回学習）
- **実装時の選択**: どちらを採用するかは未定

### 必要ファイル/成果物（ドキュメント記載）

#### 必須ファイル
1. `/backend/data/output/monthly_features.csv` (月次特徴量データ)
2. `/backend/models/monthly_landing_poisson_14d.pkl` (学習済みモデル、推論モード時)

#### 生成されるファイル
- `/backend/output/prediction_14d_{target_month}.csv` (月次着地予測結果)

#### DB入出力
- **未定義** (ドキュメントに記載なし)

### 追加メモ

- **2つのモード**: 推論のみ or 毎回学習
- **実装時の判断**: Workerでどちらを採用するか決定が必要
- **独立実行可能**: 他の予測への依存関係なし
- **実装優先度**: Phase 2（月次実績管理に必要）

---

## 7. 月次着地 21日時点 (monthly_landing_21d)

### 判定
❓ **実装されていないため不明**

**推測**: `monthly_landing_14d` と同様に2パターンあり

### 実装状況
⏳ **ホワイトリスト登録済み、スクリプト未実装**

### 入口（実行開始点）
- **ファイル**: [app/job_executor.py](app/backend/inbound_forecast_worker/app/job_executor.py)
- **関数**: `execute_job()` (line 159-189)
- **呼び出し元**: workerの `job_type == "monthly_landing_21d"` 分岐（未実装）
- **ホワイトリスト**: `ALLOWED_JOB_TYPES` (line 58)

```python
ALLOWED_JOB_TYPES = {
    "daily_tplus1",
    "daily_tplus7",
    "weekly",
    "monthly_gamma",
    "monthly_landing_14d",
    "monthly_landing_21d",  # ← ホワイトリスト登録済み
}
```

### 呼び出しチェーン（ドキュメント記載）

**ドキュメント**: `docs/development/forecast_worker_prediction_types.md:241-276`

```
execute_monthly_landing_21d() [未実装]
  ↓ subprocess
scripts/monthly_landing_gamma_poisson/run_monthly_landing_gamma_poisson.py [ファイル不在]
  ↓ オプション分岐
  ├─ --load-model: joblib.load() → 推論のみ
  └─ --use-a21: モデル学習 → 予測
```

### 学習/推論の証拠

#### A. 14日版と同じスクリプト

- ファイル不在（14日版と共通）
- `--use-a14` の代わりに `--use-a21` オプションを使用

#### B. ドキュメントの記載

**場所**: `docs/development/forecast_worker_prediction_types.md:241-276`

**コマンド例（推論のみ）**:
```bash
# 学習済みモデルで推論
python3 /backend/scripts/monthly_landing_gamma_poisson/run_monthly_landing_gamma_poisson.py \
  --monthly-csv /backend/data/output/monthly_features.csv \
  --load-model /backend/models/monthly_landing_poisson_21d.pkl \
  --out-csv /backend/output/prediction_21d.csv
```

**コマンド例（学習含む）**:
```bash
# モデル学習から実行
python3 /backend/scripts/monthly_landing_gamma_poisson/run_monthly_landing_gamma_poisson.py \
  --monthly-csv /backend/data/output/monthly_features.csv \
  --use-a21 \
  --out-csv /backend/output/prediction_21d.csv
```

### 必要ファイル/成果物（ドキュメント記載）

#### 必須ファイル
- 14日版と同じ構成
- モデルファイル: `/backend/models/monthly_landing_poisson_21d.pkl`

#### 生成されるファイル
- `/backend/output/prediction_21d_{target_month}.csv` (月次着地予測結果)

### 追加メモ

- **14日版と同じ実装パターン**: 推論のみ or 毎回学習
- **実装時の判断**: Workerでどちらを採用するか決定が必要
- **独立実行可能**: 他の予測への依存関係なし

---

## 学習スクリプトの所在確認

### 日次予測の学習スクリプト

#### train_daily_model.py

**場所**: `app/backend/inbound_forecast_worker/scripts/train_daily_model.py`

**用途**: 日次予測モデルの **事前学習**（手動実行または別ジョブ）

**証拠（学習処理）**:
```python
# line 389
model = Ridge(alpha=0.5).fit(naive.values.reshape(-1,1), y.values)

# line 412, 414
m.fit(Xt_tr, ytr.values, sample_weight=sw)
m.fit(Xt_tr, ytr.values)

# line 423, 425
m.fit(Xt_full, y.values, sample_weight=sw_full)
m.fit(Xt_full, y.values)

# line 438
meta = Ridge(alpha=0.5); meta.fit(oof_used.values, y.values)

# line 898 (保存)
joblib.dump(bundle, args.save_bundle)
```

**呼び出し元**: 
- `retrain_and_eval.py` (line 73) から呼ばれる
- 日次t+1予測のワークフローからは **呼ばれない**

#### retrain_and_eval.py

**場所**: `app/backend/inbound_forecast_worker/scripts/retrain_and_eval.py`

**用途**: `train_daily_model.py` のラッパースクリプト（学習→評価の自動化）

**証拠（subprocess呼び出し）**:
```python
# line 73-80
train_script = os.path.join(SCRIPTS_DIR, 'train_daily_model.py')
cmd = [
    sys.executable, train_script,
    '--raw-csv', daily_csv,
    '--out-dir', out_dir,
    # ...
]
p = subprocess.Popen(cmd, stdout=fh, stderr=subprocess.STDOUT)
```

**呼び出し元**: 
- 手動実行のみ
- 日次t+1予測のワークフローからは **呼ばれない**

---

## まとめ：学習有無の最終判定

### 実装済み予測（1種類）

| 予測タイプ | 判定 | 根拠 |
|-----------|------|------|
| **日次 t+1** | ✅ **推論のみ** | `joblib.load()` のみ、`.fit()` なし、学習スクリプトは別プロセス |

### 未実装予測（5種類）

| 予測タイプ | 推定判定 | 根拠 |
|-----------|---------|------|
| **日次 t+7** | ✅ **推論のみ** | t+1と同じスクリプト・モデル使用、`--future-days 7` オプションのみ |
| **月次 Gamma** | ⚠️ **毎回学習の可能性** | ドキュメント「交差検証含む」→ 学習処理あり |
| **月次 Blend** | ⚠️ **毎回学習の可能性** | ドキュメント「ブレンドモデルの学習」→ 学習処理あり |
| **週次按分** | ⚠️ **規則/按分系** | ドキュメント「按分比率を計算」→ モデル学習なし |
| **月次着地 14日** | ❓ **推論 or 学習（選択式）** | `--load-model` で推論、`--use-a14` で学習 |
| **月次着地 21日** | ❓ **推論 or 学習（選択式）** | `--load-model` で推論、`--use-a21` で学習 |

### 重要な結論

1. **実装済みは推論のみ**: 日次t+1は学習済みモデル前提の推論専用
2. **日次t+7も推論のみ**: 同じモデル・スクリプトを使用、実装容易
3. **月次系は学習の可能性**: Gamma/Blendは毎回学習の可能性が高い
4. **週次は按分系**: モデル学習なし、ルールベースの按分計算
5. **着地系は実装時に選択**: 推論のみ or 毎回学習のどちらも可能

---

## 今後の実装における推奨事項

### Phase 2: 優先実装

#### 1. daily_tplus7（推論のみ）

**理由**: 
- スクリプト実装済み（UseCase作成のみ）
- 同じモデル使用（追加学習不要）
- 実装難易度: 低

**実装方針**:
```python
def execute_daily_tplus7(db_session, target_date, job_id, timeout):
    # daily_tplus1 とほぼ同じ
    # serve_predict_model_v4_2_4.py に --future-days 7 を追加
    pass
```

#### 2. monthly_landing_14d / 21d（推論のみモード推奨）

**理由**:
- 月次実績管理に必要
- 独立実行可能
- 学習済みモデルで推論のみの方が高速（約1分）

**実装方針**:
- `--load-model` オプションを使用
- 事前にモデルを学習・保存しておく
- Worker実行時は推論のみ

### Phase 3: 月次・週次予測

#### 3. monthly_gamma → monthly_blend → weekly

**理由**:
- 短期計画に必要
- 依存関係あり（順次実行必要）

**実装方針**:
- スクリプト実装が必要
- 学習処理の有無を実装時に判定
- Gamma/Blendは毎回学習の可能性が高い

---

## 検索コマンド実行ログ

### 全体検索（job_type, execute, UseCase）

```bash
grep -rn "job_type|execute_|Run.*Forecast" app/backend/inbound_forecast_worker/app/ | head -20
```

**結果**: `job_executor.py` にホワイトリスト定義あり

### スクリプトファイル検索

```bash
find app/backend/inbound_forecast_worker/scripts/ -name "*.py"
```

**結果**:
- `serve_predict_model_v4_2_4.py` ✅
- `daily_tplus1_predict.py` ✅
- `train_daily_model.py` ✅
- `retrain_and_eval.py` ✅
- `update_daily_clean.py` ✅

### 予測関連スクリプト検索

```bash
find app/backend/inbound_forecast_worker/scripts/ -name "*gamma*"
# 結果: マッチなし

find app/backend/inbound_forecast_worker/scripts/ -name "*weekly*"
# 結果: マッチなし

find app/backend/inbound_forecast_worker/scripts/ -name "*monthly*"
# 結果: マッチなし

find app/backend/inbound_forecast_worker/scripts/ -name "*landing*"
# 結果: マッチなし

find app/backend/inbound_forecast_worker/scripts/ -name "*poisson*"
# 結果: マッチなし
```

**結論**: gamma, weekly, monthly, landing系のスクリプトは存在しない

### 学習処理検索

```bash
grep -rn "\.fit\(|joblib\.load|joblib\.dump" app/backend/inbound_forecast_worker/scripts/ | wc -l
# 結果: 26行（train_daily_model.py と serve_predict_model_v4_2_4.py のみ）
```

### future-days オプション検索

```bash
grep -n "future.days" app/backend/inbound_forecast_worker/scripts/serve_predict_model_v4_2_4.py
```

**結果**:
- line 10: ドキュメント記載
- line 331: 関数引数
- line 474: 処理内容
- line 477: ログ出力
- line 1357: argparse定義

---

## 付録: ホワイトリスト定義

**場所**: `app/backend/inbound_forecast_worker/app/job_executor.py:52-58`

```python
ALLOWED_JOB_TYPES = {
    "daily_tplus1",           # ✅ 実装済み
    "daily_tplus7",           # ⏳ 未実装（スクリプトあり）
    "weekly",                 # ⏳ 未実装
    "monthly_gamma",          # ⏳ 未実装
    "monthly_landing_14d",    # ⏳ 未実装
    "monthly_landing_21d",    # ⏳ 未実装
}
```

**実装状況**: `app/backend/inbound_forecast_worker/app/job_executor.py:185-189`

```python
if job_type == "daily_tplus1":
    execute_daily_tplus1(db_session, target_date, job_id, timeout)
else:
    # Phase 3では daily_tplus1 のみ実装
    raise JobExecutionError(
        f"Job type '{job_type}' is whitelisted but not yet implemented"
    )
```

---

## 参考資料

- [forecast_worker_prediction_types.md](docs/development/forecast_worker_prediction_types.md): 予測タイプ一覧と実行要件
- [daily_tplus1_train_or_infer_audit.md](docs/development/daily_tplus1_train_or_infer_audit.md): 日次t+1予測の学習/推論調査報告書
- [job_executor.py](app/backend/inbound_forecast_worker/app/job_executor.py): ジョブ実行エントリポイント
- [serve_predict_model_v4_2_4.py](app/backend/inbound_forecast_worker/scripts/serve_predict_model_v4_2_4.py): 日次予測推論スクリプト
- [train_daily_model.py](app/backend/inbound_forecast_worker/scripts/train_daily_model.py): 日次予測学習スクリプト

---

**調査完了日**: 2025-12-18  
**調査者**: AI Assistant  
**承認者**: （承認日時）
