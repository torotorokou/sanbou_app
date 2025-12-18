# 日次t+1予測 学習/推論 調査報告書

**調査日**: 2025-12-18  
**調査担当**: AI Assistant  
**目的**: 日次t+1予測が「毎回学習→予測」の設計なのか「推論のみ」の設計なのかを証拠付きで判定

---

## 結論

### ✅ **日次t+1は推論のみ（学習済みモデル前提）**

**ただし、オプションで残差モデルの追加学習が可能**

---

## 根拠

### 1. 入口ファイルの呼び出しチェーン

```
RunDailyTplus1ForecastUseCase (app/application/run_daily_tplus1_forecast.py)
    ↓ subprocess
daily_tplus1_predict.py (scripts/)
    ↓ subprocess
serve_predict_model_v4_2_4.py (scripts/)
    ↓ joblib.load()
model_bundle.joblib (学習済みモデル)
```

**証拠:**

| ファイル | 行番号 | 処理内容 |
|---------|--------|----------|
| `app/application/run_daily_tplus1_forecast.py` | 131-140 | subprocess で `daily_tplus1_predict.py` を呼び出し |
| `scripts/daily_tplus1_predict.py` | 49-75 | subprocess で `serve_predict_model_v4_2_4.py` を呼び出し |
| `scripts/serve_predict_model_v4_2_4.py` | 372 | `bundle = joblib.load(bundle_path)` でモデルロード |

---

### 2. 学習呼び出し箇所の調査結果

#### A. メインモデルの学習: **存在しない**

`serve_predict_model_v4_2_4.py` では：
- ✅ `joblib.load()` でモデルをロード（line 372）
- ❌ メインモデルの `.fit()` 呼び出しは **存在しない**
- ❌ `joblib.dump()` でモデルを保存する箇所も **存在しない**

**証拠コード（serve_predict_model_v4_2_4.py:372）:**
```python
bundle = joblib.load(bundle_path)
```

**結論**: メインモデルは事前学習済みのものを使用（推論のみ）

---

#### B. 残差モデルの追加学習: **オプションで存在（デフォルトOFF）**

`serve_predict_model_v4_2_4.py` には **残差再学習（residual refit）** のオプションがある：

**証拠コード（serve_predict_model_v4_2_4.py:792-855）:**
```python
if residual_refit:  # デフォルト: False
    try:
        from sklearn.ensemble import GradientBoostingRegressor
        from sklearn.linear_model import Ridge
        # 直近 90日（デフォルト）のデータで残差モデルを学習
        W = int(max(30, residual_refit_window))
        
        # 残差を計算
        resid_target = y_hist_full - base_pred_hist_full
        X_resid = hist_feat_for_resid.values
        
        # 残差モデルの学習
        if residual_model.lower() == "ridge":
            m = Ridge(alpha=2.0)
        else:
            m = GradientBoostingRegressor(
                loss="absolute_error", n_estimators=200, learning_rate=0.04,
                max_depth=2, subsample=0.8, random_state=42
            )
        
        # fit() 実行（学習）
        m.fit(X_resid, resid_target, sample_weight=sw)
        
        resid_model = m
        print(f"[INFO] residual-refit enabled: model={residual_model} window={W} rows={len(X_resid)}")
    except Exception as e:
        print(f"[WARN] residual-refit failed: {e}")
```

**コマンドラインオプション（line 1384-1385）:**
```python
ap.add_argument("--residual-refit", action="store_true", help="直近期の残差を軽量モデルで再学習して将来に加算")
ap.add_argument("--residual-refit-window", type=int, default=90, help="残差再学習に使う直近期の日数")
```

**現在の実装での使用状況:**
- ❌ `run_daily_tplus1_forecast.py` では `--residual-refit` を **渡していない**
- ❌ `daily_tplus1_predict.py` でも `--residual-refit` を **渡していない**

**検証コマンド:**
```bash
grep -n "residual" app/backend/inbound_forecast_worker/app/application/run_daily_tplus1_forecast.py
# 結果: マッチなし

grep -n "residual" app/backend/inbound_forecast_worker/scripts/daily_tplus1_predict.py
# 結果: マッチなし
```

**結論**: 残差再学習のコードは存在するが、現在の実装では **使用されていない**

---

### 3. モデル保存の有無

#### A. `serve_predict_model_v4_2_4.py` での保存: **存在しない**

```bash
grep -n "joblib.dump\|pickle.dump" scripts/serve_predict_model_v4_2_4.py
# 結果: マッチなし
```

**結論**: 推論スクリプトはモデルを保存しない（読み込み専用）

---

#### B. 学習スクリプト `train_daily_model.py` での保存: **存在する（別用途）**

`train_daily_model.py` は **学習専用スクリプト** であり、日次t+1予測のワークフローからは **呼ばれていない**。

**証拠（train_daily_model.py:898）:**
```python
if args.save_bundle:
    # ... バンドルの構築 ...
    joblib.dump(bundle, args.save_bundle)
    print(f"[SAVED] bundle: {args.save_bundle}")
```

**用途:**
- 事前の学習フェーズでモデルを作成・保存
- 出力: `model_bundle.joblib`, `res_walkforward.csv`
- 実行タイミング: **手動実行または別の学習ジョブ**

**日次t+1予測からの呼び出し確認:**
```bash
grep -rn "train_daily_model" app/backend/inbound_forecast_worker/app/
# 結果: マッチなし（呼び出しなし）
```

**結論**: `train_daily_model.py` は日次t+1予測のフローには含まれない

---

### 4. subprocess で学習を呼んでいる箇所

#### A. `daily_tplus1_predict.py` → `serve_predict_model_v4_2_4.py`

**証拠（daily_tplus1_predict.py:49-75）:**
```python
serve_path = os.path.join(os.path.dirname(__file__), 'serve_predict_model_v4_2_4.py')
cmd = [sys.executable, serve_path,
       '--bundle', args.bundle,
       '--out-csv', args.out_csv,
       '--future-days', '1']
# ... 予約データ等のオプション追加 ...
# --residual-refit は追加されない ❌

print('[INFO] launching serve script:', ' '.join(cmd))
proc = subprocess.run(cmd, capture_output=True, text=True)
```

**渡されるコマンド例:**
```bash
python3 serve_predict_model_v4_2_4.py \
  --bundle /backend/models/final_fast_balanced/model_bundle.joblib \
  --res-walk-csv /backend/models/final_fast_balanced/res_walkforward.csv \
  --out-csv /backend/output/tplus1_pred.csv \
  --future-days 1 \
  --start-date 2025-12-19 \
  --reserve-default-count 0.0 \
  --reserve-default-sum 0.0 \
  --reserve-default-fixed 0.0
```

**注目点:**
- ✅ `--bundle` でモデルパスを指定（既存モデル前提）
- ❌ `--residual-refit` は **含まれない**

---

#### B. `RunDailyTplus1ForecastUseCase` → `daily_tplus1_predict.py`

**証拠（app/application/run_daily_tplus1_forecast.py:131-147）:**
```python
cmd = [
    "python3",
    str(self._script_path),
    "--bundle", str(self._model_bundle_path),
    "--res-walk-csv", str(self._res_walk_csv_path),
    "--out-csv", str(output_csv_path),
    "--start-date", target_date.isoformat(),
]

if reserve_csv_path:
    cmd += [
        "--reserve-csv", str(reserve_csv_path),
        "--reserve-date-col", "予約日",
        "--reserve-count-col", "台数",
        "--reserve-fixed-col", "固定客",
    ]

logger.info(f"Executing prediction script: {' '.join(cmd)}")

result = subprocess.run(
    cmd,
    capture_output=True,
    text=True,
    timeout=self._timeout,
    check=False,
    cwd="/backend"
)
```

**注目点:**
- ✅ モデルバンドルパスを渡す（既存モデル前提）
- ❌ 学習関連のオプションは **含まれない**

---

## 追加の疑い

### 残差モデルだけの部分学習（オプション機能）

**状況:**
- `serve_predict_model_v4_2_4.py` には `--residual-refit` オプションが実装済み
- 直近90日（デフォルト）のデータで残差モデル（Ridge or GBR）を追加学習
- メインモデル（Stage1品目別 + Stage2統合）は変更しない

**現在の使用状況:**
- ❌ 日次t+1予測のワークフローでは **使用されていない**
- ⚠️ 手動実行や別のワークフローで有効化可能

**有効化する場合の影響:**

```python
# run_daily_tplus1_forecast.py の変更例（実装されていない）
cmd = [
    "python3",
    str(self._script_path),
    "--bundle", str(self._model_bundle_path),
    "--res-walk-csv", str(self._res_walk_csv_path),
    "--out-csv", str(output_csv_path),
    "--start-date", target_date.isoformat(),
    "--residual-refit",  # ← これを追加すると残差学習が有効化
    "--residual-refit-window", "90",
]
```

**残差学習の処理時間:**
- 推定: 数秒〜10秒程度（90日分のデータで軽量モデル学習）
- メインモデルの学習（1時間〜）と比較して非常に軽量

---

## 別の学習スクリプトの存在確認

### `train_daily_model.py` の詳細

**ファイル:** `app/backend/inbound_forecast_worker/scripts/train_daily_model.py`

**用途:**
- 日次実数予測モデルの **事前学習**
- Walk-forward検証
- モデルバンドルの保存

**実行方法（手動）:**
```bash
python train_daily_model.py \
  --raw-csv /path/to/receive_data.csv \
  --out-dir /path/to/output \
  --save-bundle /path/to/model_bundle.joblib \
  --top-n 6 \
  --n-splits 3 \
  --retrain-interval 7 \
  --n-jobs -1
```

**出力:**
- `model_bundle.joblib`: 学習済みモデル
- `res_walkforward.csv`: Walk-forward検証結果
- `scores_walkforward.json`: 精度指標
- その他メタデータ・プロット

**日次t+1予測からの呼び出し:**
- ❌ **呼び出しなし**
- `grep -rn "train_daily_model" app/backend/inbound_forecast_worker/app/` → マッチなし

**位置づけ:**
- 定期的な学習ジョブ（週次/月次）で実行される想定
- または、モデルの初回作成・更新時に手動実行

---

### `retrain_and_eval.py` の詳細

**ファイル:** `app/backend/inbound_forecast_worker/scripts/retrain_and_eval.py`

**用途:**
- `train_daily_model.py` のラッパースクリプト
- CSV形式の変換を担当
- 学習→評価の自動化

**呼び出し構造（retrain_and_eval.py:73-80）:**
```python
train_script = os.path.join(SCRIPTS_DIR, 'train_daily_model.py')
# ...
cmd = [
    sys.executable, train_script,
    '--raw-csv', daily_csv,
    '--out-dir', out_dir,
    # ... 他のオプション ...
]
p = subprocess.Popen(cmd, stdout=fh, stderr=subprocess.STDOUT)
```

**日次t+1予測からの呼び出し:**
- ❌ **呼び出しなし**

---

## 調査結果サマリー

### 検索実行結果

#### 学習関連キーワード検索

```bash
# 実行コマンド
grep -rn "\.fit\(|residual.refit|joblib\.dump|train_daily|walkforward" \
  app/backend/inbound_forecast_worker/

# 結果サマリー
```

| キーワード | マッチ箇所 | 用途 |
|-----------|-----------|------|
| `.fit(` | `scripts/train_daily_model.py` (19箇所) | 学習スクリプト（別用途） |
| `.fit(` | `scripts/serve_predict_model_v4_2_4.py` (4箇所) | 残差再学習（オプション、未使用） |
| `residual_refit` | `scripts/serve_predict_model_v4_2_4.py` (7箇所) | 残差再学習（オプション、未使用） |
| `joblib.dump` | `scripts/train_daily_model.py` (1箇所) | 学習後のモデル保存（別用途） |
| `subprocess.run` | `scripts/daily_tplus1_predict.py` (1箇所) | serve スクリプト呼び出し |
| `subprocess.run` | `app/application/run_daily_tplus1_forecast.py` (1箇所) | daily スクリプト呼び出し |

**重要な発見:**
- ✅ 日次t+1予測の **本流には学習処理が存在しない**
- ✅ 残差再学習はオプション機能だが **現在は使用されていない**
- ✅ `train_daily_model.py` は別プロセス（事前学習）

---

### ファイル探索結果

```bash
# 実行コマンド
find app/backend/inbound_forecast_worker/scripts/ -name "*train*.py" -o -name "*fit*.py" -o -name "*build*.py"

# 結果
```

| ファイル名 | 用途 | 日次t+1から呼ばれるか |
|-----------|------|---------------------|
| `train_daily_model.py` | 学習専用スクリプト | ❌ 呼ばれない |
| `retrain_and_eval.py` | 学習ラッパー | ❌ 呼ばれない |

**結論:** 日次t+1予測のワークフローには学習スクリプトは含まれない

---

## 最終判定

### ✅ **日次t+1は推論のみ（学習済みモデル前提）**

**明確な根拠:**

1. **メインモデルは事前学習済み**
   - `joblib.load()` でモデルをロード
   - `.fit()` の呼び出しなし
   - `joblib.dump()` でモデルを保存する箇所なし

2. **subprocess呼び出しにも学習処理なし**
   - `daily_tplus1_predict.py` → `serve_predict_model_v4_2_4.py`
   - どちらも推論専用
   - `--residual-refit` オプションは **渡されていない**

3. **学習スクリプトは別プロセス**
   - `train_daily_model.py` は事前学習用（手動実行または別ジョブ）
   - 日次t+1予測のワークフローからは **呼ばれない**

---

## 追加情報: 残差再学習（オプション）

### 現状

- ❌ **使用されていない**
- コードは存在するが、コマンドラインオプションで有効化されていない

### 有効化した場合の動作

**処理内容:**
1. メインモデル（学習済み）で予測実行
2. 直近90日の実績と予測の残差を計算
3. 残差モデル（Ridge or GBR）を学習
4. 将来予測に残差補正を適用

**処理時間:**
- 推定: 数秒〜10秒程度（軽量）

**精度への影響:**
- 最新データへの適応性向上（理論上）
- 実測データでの効果は未検証

**実装方法:**

```python
# app/application/run_daily_tplus1_forecast.py の修正（案）
cmd = [
    "python3",
    str(self._script_path),
    "--bundle", str(self._model_bundle_path),
    "--res-walk-csv", str(self._res_walk_csv_path),
    "--out-csv", str(output_csv_path),
    "--start-date", target_date.isoformat(),
    "--residual-refit",  # ← 追加
    "--residual-refit-window", "90",  # ← 追加
    "--residual-model", "gbr",  # ← 追加（デフォルト）
]
```

---

## 推奨事項

### 短期（現状維持）

✅ **現在の設計（推論のみ）を維持**

**理由:**
- 予測速度が速い（数秒）
- 既存モデルの精度が十分
- 運用がシンプル

**前提条件:**
- モデルファイル（`model_bundle.joblib`）が配置済み
- 定期的なモデル更新の仕組みが別途存在

---

### 中期（残差再学習の導入検討）

⚠️ **`--residual-refit` の有効化を検討**

**メリット:**
- 最新データへの適応
- メインモデルは再学習不要
- 処理時間の増加は軽微（数秒）

**デメリット:**
- 精度への影響が未検証
- ログ・監視の追加が必要

**検証方法:**
1. 開発環境で `--residual-refit` を有効化
2. 過去データでの精度比較（Walk-forward）
3. 運用環境での段階的導入

---

### 長期（定期学習の自動化）

📅 **週次/月次の学習ジョブを実装**

**設計案:**
1. **定期学習ジョブ（週次/月次）**
   - `train_daily_model.py` を実行
   - 新しいモデルバンドルを生成
   - GCS等に保存

2. **予測ジョブ（日次）**
   - 最新モデルをロード
   - 推論実行（高速）

3. **モデルバージョン管理**
   - バージョン番号付きで保存
   - ロールバック可能な設計

**参考実装:**
```bash
# 週次学習ジョブ（cron or k8s CronJob）
0 2 * * 1 python /backend/scripts/train_daily_model.py \
  --raw-csv /data/receive_latest.csv \
  --out-dir /models/v$(date +%Y%m%d) \
  --save-bundle /models/v$(date +%Y%m%d)/model_bundle.joblib
```

---

## 付録

### 関連ファイル一覧

| ファイル | 役割 | 学習/推論 |
|---------|------|----------|
| `app/application/run_daily_tplus1_forecast.py` | UseCase（オーケストレーション） | 推論のみ |
| `scripts/daily_tplus1_predict.py` | ランチャー | 推論のみ |
| `scripts/serve_predict_model_v4_2_4.py` | 推論エンジン | 推論のみ（残差学習オプション有り） |
| `scripts/train_daily_model.py` | 学習専用スクリプト | 学習のみ（別プロセス） |
| `scripts/retrain_and_eval.py` | 学習ラッパー | 学習のみ（別プロセス） |

---

### 検索コマンド実行ログ

```bash
# 学習関連キーワード検索
grep -rn "\.fit\(|residual.refit|joblib\.dump|train_daily|walkforward" \
  app/backend/inbound_forecast_worker/ | grep -v "\.pyc" | grep -v "__pycache__"

# subprocess 呼び出し検索
grep -rn "subprocess\.run|subprocess\.Popen" \
  app/backend/inbound_forecast_worker/ | grep -v "\.pyc"

# モデルロード検索
grep -rn "joblib\.load" \
  app/backend/inbound_forecast_worker/scripts/serve_predict_model_v4_2_4.py

# 残差再学習オプション検索
grep -rn "residual" \
  app/backend/inbound_forecast_worker/app/application/run_daily_tplus1_forecast.py
# → マッチなし（未使用）

grep -rn "residual" \
  app/backend/inbound_forecast_worker/scripts/daily_tplus1_predict.py
# → マッチなし（未使用）
```

---

## 結論（再掲）

### ✅ 日次t+1は推論のみ（学習済みモデル前提）

**根拠:**
1. メインモデルは `joblib.load()` でロードするのみ
2. `.fit()` 呼び出しは存在しない（残差再学習を除く）
3. `--residual-refit` オプションは未使用
4. `train_daily_model.py` は別プロセス（日次t+1から呼ばれない）

**例外:**
- 残差再学習（`--residual-refit`）は実装済みだが **現在は未使用**
- 有効化すると直近90日で残差モデルのみ追加学習（メインモデルは不変）

---

**調査完了日**: 2025-12-18  
**調査者**: AI Assistant  
**承認者**: （承認日時）
