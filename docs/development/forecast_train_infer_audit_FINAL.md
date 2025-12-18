# 全予測機能 学習/推論 最終監査報告書

**調査日**: 2025-12-18  
**調査担当**: AI Assistant  
**目的**: inbound_forecast_worker の全機能について「学習」と「推論」の実態を包括的に調査

---

## エグゼクティブサマリー

### 重要な発見

✅ **inbound_forecast_worker の真の目的**:
- README.mdに明記: 「**再学習・評価・将来予測**を単体で完結させること」
- このworkerは**学習機能**と**推論機能**の両方を持つ設計

### Worker実装状況 vs スクリプト実装状況

| 予測タイプ | Worker実装 | スクリプト実装 | 学習機能 | 推論機能 |
|-----------|-----------|--------------|---------|---------|
| 日次 t+1 | ✅ 推論のみ | ✅ 学習+推論 | ⏸️ 未統合 | ✅ 実装済み |
| 日次 t+7 | ❌ 未実装 | ✅ 学習+推論 | ⏸️ 未統合 | ⚠️ 可能 |
| 月次 Gamma | ❌ 未実装 | ✅ 学習+推論 | ⏸️ 未統合 | ⚠️ 可能 |
| 月次 Blend | ❌ 未実装 | ✅ 学習+推論 | ⏸️ 未統合 | ⚠️ 可能 |
| 週次按分 | ❌ 未実装 | ✅ 按分のみ | ❌ なし | ⚠️ 可能 |
| 月次着地14日 | ❌ 未実装 | ✅ 学習+推論 | ⏸️ 未統合 | ⚠️ 可能 |
| 月次着地21日 | ❌ 未実装 | ✅ 学習+推論 | ⏸️ 未統合 | ⚠️ 可能 |

### 結論

1. **スクリプトレベル**: すべての予測で学習・推論の両方が実装済み（週次を除く）
2. **Workerレベル**: 日次t+1の推論のみが実装済み
3. **設計思想**: README.mdは「再学習」を重視しているが、Workerは「推論のみ」実装
4. **乖離の存在**: スクリプト（学習重視）とWorker（推論重視）で設計思想が異なる

---

## 1. inbound_forecast_worker の設計思想

### README.mdに記載された目的

**引用**:
```markdown
## 目的

- 日次 / 週次 / 月次（Gamma + ブレンド）/ 月次着地モデルの **再学習・評価・将来予測** を、
   `submission_release_20251027` フォルダ単体で完結させること。
```

**推奨実行順序**:
1. **日次モデルの再学習**
2. **月次 Gamma + ブレンドの再学習＋将来予測**
3. 週次モデル（Gamma+ブレンド月次予測の按分）による週次推論
4. 月次着地モデル（第1〜2週から月合計）の評価・単月推論

### 設計思想の解釈

✅ **想定される運用フロー**:

```
定期学習ジョブ（週次/月次）
  ↓
  retrain_and_eval.py → train_daily_model.py
  ↓
  model_bundle.joblib 更新
  ↓
日次予測ジョブ（毎日）
  ↓
  daily_tplus1_predict.py → serve_predict_model_v4_2_4.py
  ↓
  学習済みモデルで推論
```

---

## 2. 詳細調査結果

---

### 2.1. 日次予測（Daily）

#### A. 学習機能（スクリプト実装済み、Worker未統合）

**スクリプト**: `scripts/retrain_and_eval.py`

**README.mdの記載**:
```markdown
- `scripts/retrain_and_eval.py`
   - 日次モデルの再学習→評価→推論を一括で実行するラッパー（短時間の "--quick" モードあり）。
```

**実行例（README.md記載）**:
```bash
# クイック再学習
python3 ./scripts/retrain_and_eval.py --quick

# フル再学習
python3 ./scripts/retrain_and_eval.py
```

**呼び出しチェーン**:
```
retrain_and_eval.py (line 73)
  ↓ subprocess
train_daily_model.py
  ↓ .fit() 複数回（line 389, 412, 414, 423, 438等）
  ↓ joblib.dump() (line 898)
model_bundle.joblib 生成
```

**処理時間**:
- クイック: 約18分10秒（docs.md記載）
- フル: 数時間（bootstrap回数による）

**Worker統合状況**: ❌ 未統合（手動実行のみ）

#### B. 推論機能（スクリプト実装済み、Worker実装済み）

**スクリプト**: `scripts/daily_tplus1_predict.py`

**README.mdの記載**:
```markdown
- `scripts/serve_predict_model_v4_2_4.py`, `scripts/daily_tplus1_predict.py`
   - 学習済み日次バンドルから t+1 / t+7 予測を実行。
```

**呼び出しチェーン**:
```
daily_tplus1_predict.py
  ↓ subprocess
serve_predict_model_v4_2_4.py
  ↓ joblib.load() (line 372)
model_bundle.joblib ロード
  ↓ predict()
予測結果出力
```

**Worker統合状況**: ✅ 実装済み（`execute_daily_tplus1()`）

#### 判定

| 機能 | 実装状況 | Worker統合 | 判定 |
|-----|---------|-----------|------|
| **学習** | ✅ スクリプト実装済み | ❌ 未統合 | **毎回学習可能（未使用）** |
| **推論** | ✅ スクリプト実装済み | ✅ 実装済み | **推論のみ（現状）** |

---

### 2.2. 月次予測 Gamma（Monthly Gamma）

#### A. 学習機能（スクリプト実装済み、Worker未統合）

**スクリプト**: `scripts/gamma_recency_model/gamma_recency_model.py`

**README.mdの記載**:
```markdown
- `scripts/gamma_recency_model/gamma_recency_model.py`
   - Gamma Recency ベースの月次モデル本体（再学習・評価・将来予測）。

#### Gamma Recency モデルの再学習＋将来予測

python3 ./scripts/gamma_recency_model/gamma_recency_model.py
```

**学習処理の証拠**:
- line 612: `model.fit(train_df)` （交差検証）
- line 1108: `model.fit(train_df)` （最終学習）
- line 1570-1571: `joblib.dump(model, gamma_path)` （モデル保存）

**処理時間**: 約10〜20分（交差検証含む、docs.md記載）

**Worker統合状況**: ❌ 未統合（ホワイトリスト登録済み）

#### B. 推論機能（保存モデルあり、Worker未統合）

- 学習時にモデル保存 → 次回実行時に使用可能
- ただし、README.mdは「再学習＋将来予測」を推奨（毎回学習前提）

#### 判定

| 機能 | 実装状況 | Worker統合 | 判定 |
|-----|---------|-----------|------|
| **学習** | ✅ スクリプト実装済み | ❌ 未統合 | **毎回学習（設計通り）** |
| **推論** | ⚠️ モデル保存可能 | ❌ 未統合 | **推論可能（非推奨）** |

---

### 2.3. 月次予測 Blend（Monthly Blend）

#### A. 学習機能（スクリプト実装済み、Worker未統合）

**スクリプト**: `scripts/gamma_recency_model/blend_lgbm.py`

**README.mdの記載**:
```markdown
- `scripts/gamma_recency_model/blend_lgbm.py`
   - Gamma 出力に対する Ridge/LGBM ブレンドモデル（再学習・評価・将来予測）。

#### Gamma 出力に対する Ridge/LGBM ブレンドモデルの再学習＋将来予測

python3 ./scripts/gamma_recency_model/blend_lgbm.py
```

**学習処理の証拠**:
- line 80: `model.fit(train_df)` （Gamma学習）
- line 159: `ridge.fit(X_train, y_train)` （Ridge学習）
- line 180: `lgbm.fit(X_train, y_train)` （LGBM学習）

**処理時間**: 約5〜10分（docs.md記載）

**Worker統合状況**: ❌ 未統合（ホワイトリスト未登録）

#### 判定

| 機能 | 実装状況 | Worker統合 | 判定 |
|-----|---------|-----------|------|
| **学習** | ✅ スクリプト実装済み | ❌ 未統合 | **毎回学習（設計通り）** |

---

### 2.4. 週次予測 按分（Weekly Allocation）

#### A. 按分機能（スクリプト実装済み、Worker未統合）

**スクリプト**: `scripts/weekly_allocation/allocate_monthly_to_weekly_from_blend.py`

**README.mdの記載**:
```markdown
- `scripts/weekly_allocation/weekly_allocation.py`, `scripts/weekly_allocation/allocate_monthly_to_weekly_from_blend.py`
   - 月次予測（Gamma + ブレンド）の月合計を、過去の月内週別構成比で按分する週次モデル。

週次モデルは、日次残差スタックではなく **月次予測（Gamma + ブレンド）の月合計を週別構成比で按分する単純化モデル** を採用しています。
```

**処理内容**:
- 履歴から週次シェア計算（`compute_weekly_share_from_history()`）
- 月次予測を按分（`allocate_monthly_to_weekly()`）
- **モデル学習なし**

**処理時間**: 約2〜5分（docs.md記載）

**Worker統合状況**: ❌ 未統合（ホワイトリスト登録済み）

#### 判定

| 機能 | 実装状況 | Worker統合 | 判定 |
|-----|---------|-----------|------|
| **按分** | ✅ スクリプト実装済み | ❌ 未統合 | **規則/按分のみ（学習なし）** |

---

### 2.5. 月次着地予測（Monthly Landing）

#### A. 学習機能（スクリプト実装済み、Worker未統合）

**スクリプト**: `scripts/monthly_landing_gamma_poisson/run_monthly_landing_gamma_poisson.py`

**README.mdの記載**:
```markdown
- `scripts/monthly_landing_gamma_poisson/run_monthly_landing_gamma_poisson.py`
   - 月次着地予測モジュール（Gamma/Poisson版）。
   - 第1〜2週（および21日）実績から月合計を推定します。

#### 一括実行（データ作成・学習・推論）

./run_monthly_landing_pipeline.sh

- **データ作成**: `data/input/01_daily_clean.csv` -> `data/output/monthly_features.csv`
- **学習**: 14日版・21日版モデルを学習し `models/` に保存
- **推論**: 保存済みモデルで推論し `output/` に結果出力
```

**学習処理の証拠**:
- line 110: `model.fit(X, y)` （Poisson/Tweedie回帰）
- line 174: `joblib.dump(artifact, save_path)` （モデル保存）

**2つのモード**:
1. **学習モード**: `--use-a14` / `--use-a21` （約5〜10分）
2. **推論モード**: `--load-model` （約1分）

**Worker統合状況**: ❌ 未統合（ホワイトリスト登録済み）

#### 判定

| 機能 | 実装状況 | Worker統合 | 判定 |
|-----|---------|-----------|------|
| **学習** | ✅ スクリプト実装済み | ❌ 未統合 | **毎回学習 or 推論（選択式）** |

---

## 3. 包括的まとめ

### 3.1. スクリプトレベルの実態

| 予測タイプ | 学習機能 | 推論機能 | README.md記載 | 設計思想 |
|-----------|---------|---------|--------------|---------|
| 日次 t+1 | ✅ 実装済み | ✅ 実装済み | ✅ 再学習明記 | **学習+推論** |
| 日次 t+7 | ✅ 実装済み | ✅ 実装済み | ✅ 推論明記 | **学習+推論** |
| 月次 Gamma | ✅ 実装済み | ⚠️ 可能 | ✅ 再学習明記 | **毎回学習** |
| 月次 Blend | ✅ 実装済み | ⚠️ 可能 | ✅ 再学習明記 | **毎回学習** |
| 週次按分 | ❌ なし | ✅ 実装済み | ✅ 按分明記 | **按分のみ** |
| 月次着地14日 | ✅ 実装済み | ✅ 実装済み | ✅ 学習明記 | **学習+推論** |
| 月次着地21日 | ✅ 実装済み | ✅ 実装済み | ✅ 学習明記 | **学習+推論** |

### 3.2. Workerレベルの実態

| 予測タイプ | Worker実装 | 実装内容 | 学習統合 | 推論統合 |
|-----------|-----------|---------|---------|---------|
| 日次 t+1 | ✅ 実装済み | `execute_daily_tplus1()` | ❌ 未統合 | ✅ 実装済み |
| 日次 t+7 | ❌ 未実装 | `execute_daily_tplus7()` 未作成 | ❌ 未統合 | ❌ 未統合 |
| 月次 Gamma | ❌ 未実装 | `execute_monthly_gamma()` 未作成 | ❌ 未統合 | ❌ 未統合 |
| 月次 Blend | ❌ 未実装 | 未作成 | ❌ 未統合 | ❌ 未統合 |
| 週次按分 | ❌ 未実装 | `execute_weekly()` 未作成 | - | ❌ 未統合 |
| 月次着地14日 | ❌ 未実装 | `execute_monthly_landing_14d()` 未作成 | ❌ 未統合 | ❌ 未統合 |
| 月次着地21日 | ❌ 未実装 | `execute_monthly_landing_21d()` 未作成 | ❌ 未統合 | ❌ 未統合 |

### 3.3. 設計思想の乖離

#### README.md（スクリプトレベル）の思想

✅ **「再学習」を重視**
- 目的に「再学習・評価・将来予測」を明記
- 推奨実行順序の第一ステップが「日次モデルの再学習」
- すべてのスクリプトが学習機能を実装

#### Workerの実装思想

✅ **「推論のみ」を実装**
- 実装済みは日次t+1の推論のみ
- 学習ジョブは実装されていない
- 学習済みモデルの存在を前提とした設計

#### 乖離の理由（推測）

1. **運用フロー分離**:
   - 学習: 手動実行または別ジョブ（週次/月次バッチ）
   - 推論: Workerが自動実行（日次/リアルタイム）

2. **Phase分割**:
   - Phase 1-3: 推論機能の実装（現在完了）
   - Phase 4以降: 学習機能のWorker統合（未着手）

---

## 4. 実行可能なシェルスクリプト

### 4.1. 発見されたシェルスクリプト

| スクリプト | 用途 | 存在確認 |
|----------|------|---------|
| `run_monthly_landing_pipeline.sh` | 月次着地モデルの一括実行 | ✅ |
| `run_monthly_gamma_blend.sh` | 月次Gamma+Blendの一括実行 | ✅ |
| `run_weekly_allocation.sh` | 週次按分の実行 | ✅ |
| `reproduce_daily_speedup.sh` | 日次モデル高速再現 | ✅ |

### 4.2. README.mdの実行例

#### 日次モデル

```bash
# クイック再学習（18分10秒）
python3 ./scripts/retrain_and_eval.py --quick

# フル再学習
python3 ./scripts/retrain_and_eval.py
```

#### 月次 Gamma

```bash
# 再学習＋将来予測（10〜20分）
python3 ./scripts/gamma_recency_model/gamma_recency_model.py
```

#### 月次 Blend

```bash
# 再学習＋将来予測（5〜10分）
python3 ./scripts/gamma_recency_model/blend_lgbm.py
```

#### 週次按分

```bash
# 按分実行（2〜5分）
./run_weekly_allocation.sh
```

#### 月次着地

```bash
# 一括実行（データ作成・学習・推論）
./run_monthly_landing_pipeline.sh

# 個別実行（21日版学習）
python3 scripts/monthly_landing_gamma_poisson/run_monthly_landing_gamma_poisson.py \
  --monthly-csv data/output/monthly_features.csv \
  --use-a21 \
  --save-model models/monthly_landing_poisson_21d.pkl
```

---

## 5. 最終判定

### 5.1. 各予測の学習/推論判定（スクリプトレベル）

| 予測タイプ | 判定 | 根拠 |
|-----------|------|------|
| **日次 t+1** | ⚠️ **学習+推論（両方実装）** | retrain_and_eval.py で学習、daily_tplus1_predict.py で推論 |
| **日次 t+7** | ⚠️ **学習+推論（両方実装）** | 日次t+1と同じモデル、--future-days 7 で実行 |
| **月次 Gamma** | ⚠️ **毎回学習** | README.md「再学習＋将来予測」明記、.fit() 複数回 |
| **月次 Blend** | ⚠️ **毎回学習** | README.md「再学習＋将来予測」明記、Ridge+LGBM学習 |
| **週次按分** | ✅ **規則/按分のみ** | モデル学習なし、履歴パターンで按分 |
| **月次着地14日** | ⚠️ **学習 or 推論（選択式）** | --use-a14 で学習、--load-model で推論 |
| **月次着地21日** | ⚠️ **学習 or 推論（選択式）** | --use-a21 で学習、--load-model で推論 |

### 5.2. 各予測の学習/推論判定（Workerレベル）

| 予測タイプ | 判定 | 根拠 |
|-----------|------|------|
| **日次 t+1** | ✅ **推論のみ** | execute_daily_tplus1() は推論のみ実装 |
| **日次 t+7** | ⏳ **未実装** | スクリプトあり、UseCase未作成 |
| **月次 Gamma** | ⏳ **未実装** | スクリプトあり、UseCase未作成 |
| **月次 Blend** | ⏳ **未実装** | スクリプトあり、UseCase未作成 |
| **週次按分** | ⏳ **未実装** | スクリプトあり、UseCase未作成 |
| **月次着地14日** | ⏳ **未実装** | スクリプトあり、UseCase未作成 |
| **月次着地21日** | ⏳ **未実装** | スクリプトあり、UseCase未作成 |

---

## 6. 推奨される今後の実装方針

### Phase 4: 学習ジョブのWorker統合

#### 6.1. 新しいjob_typeの追加

```python
ALLOWED_JOB_TYPES = {
    # 推論ジョブ
    "daily_tplus1",
    "daily_tplus7",
    "weekly",
    "monthly_gamma",
    "monthly_landing_14d",
    "monthly_landing_21d",
    
    # 学習ジョブ（新規）
    "train_daily_model",
    "train_monthly_gamma",
    "train_monthly_blend",
    "train_monthly_landing_14d",
    "train_monthly_landing_21d",
}
```

#### 6.2. 学習UseCaseの実装例

```python
def execute_train_daily_model(db_session, job_id, timeout):
    """日次モデルの再学習"""
    cmd = [
        "python3",
        "/backend/scripts/retrain_and_eval.py",
        "--quick",  # or フル学習
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    # モデルファイル更新確認
    # DB記録（学習完了時刻、精度指標等）
```

#### 6.3. スケジューリング

```python
# 学習ジョブ: 週次実行（日曜深夜）
schedule.every().sunday.at("02:00").do(
    create_forecast_job, 
    job_type="train_daily_model"
)

# 推論ジョブ: 毎日実行（朝7時）
schedule.every().day.at("07:00").do(
    create_forecast_job, 
    job_type="daily_tplus1"
)
```

---

## 7. docs.md と README.md の整合性確認

### 7.1. docs.mdの記載

✅ **正確**
- 記載されているスクリプトはすべて実在
- コマンド例も実行可能
- 精度指標も妥当

### 7.2. README.mdの記載

✅ **正確かつ詳細**
- 「再学習」の重要性を強調
- 推奨実行順序を明示
- 処理時間の記載あり
- シェルスクリプトの説明あり

### 7.3. 両者の関係

- **docs.md**: 実行コマンド一覧（技術詳細）
- **README.md**: 設計思想と運用方針（ビジネス視点）
- **整合性**: 完全に一致、矛盾なし

---

## 8. 謝罪と訂正

### 初回調査の誤り

❌ **誤った結論（初回）**: 
- 「gamma, weekly, landing系のスクリプトは存在しない」
- 「月次系は毎回学習の可能性」→ 推測レベル

✅ **正しい結論（最終）**:
- **すべてのスクリプトが実在**
- **README.mdに「再学習」が明記**
- **学習機能は実装済み、Worker未統合**

### 見落とした理由

1. サブディレクトリを確認しなかった
2. README.mdを精読しなかった
3. 「推論のみ」という先入観があった

---

## 9. 結論

### スクリプトレベルの真実

✅ **すべての予測で学習機能が実装済み**（週次を除く）
- 日次: `retrain_and_eval.py` → `train_daily_model.py`
- 月次Gamma: `gamma_recency_model.py`（再学習明記）
- 月次Blend: `blend_lgbm.py`（再学習明記）
- 月次着地: `run_monthly_landing_gamma_poisson.py`（学習+推論）

### Workerレベルの現実

⚠️ **推論機能のみが実装済み**（日次t+1のみ）
- 学習ジョブはWorkerに統合されていない
- 学習は手動実行または別ジョブで実施する想定

### 設計思想の解釈

✅ **2段階の運用フロー**:
1. **定期学習フェーズ**（週次/月次）: スクリプト直接実行
2. **日次推論フェーズ**（毎日）: Worker自動実行

---

**調査完了日**: 2025-12-18（最終版）  
**調査者**: AI Assistant  
**承認**: README.md と docs.md の記載はすべて正確であることを確認
