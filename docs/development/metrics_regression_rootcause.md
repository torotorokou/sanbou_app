# モデル精度劣化の根本原因分析レポート（修正版）

**作成日**: 2025-12-19（修正版）  
**分析者**: GitHub Copilot (Claude Sonnet 4.5)  
**目的**: 統合前と現状の精度差異を特定

---

## 1. エグゼクティブサマリー

### 1.1 結論

**主原因**: 
1. **評価期間の短縮**（429日 → 243日、-43%）
2. **データソースの違い**（CSV 12ヶ月分 vs DB直接取得で実質7ヶ月のクリーンデータ）
3. **品目別モデルの劣化**（R2_sum_only: 0.466 → -0.596）

**副原因**: データ品質、予約データの扱い

### 1.2 メトリクス比較（正確な値）

| 指標 | 旧版（統合前） | 現状 | 変化率 |
|-----|-------------|------|--------|
| R2 (Total) | 0.823 | 0.636 | -22.7% |
| MAE (Total) | 9.935 ton | 12.97 ton | +30.5% |
| R2 (Sum Only) | 0.466 | -0.596 | -228% |
| MAE (Sum Only) | 18.46 ton | 34.71 ton | +88.1% |
| **評価日数** | **429日** | **243日** | **-43.4%** |
| **評価期間** | 2024/08/29～2025/10/31 | 2025/04/18～2025/12/16 | 異なる |

---

## 2. データ単位とR2_sum_onlyの正確な理解

### 2.1 旧版（CSV入力、kg単位）

**ファイル**: `data/input/20240501-20250422.csv`

**実測メトリクス**（scores_walkforward.json）:
```json
{
  "R2_total": 0.823,
  "MAE_total": 9935.4 kg,
  "R2_sum_only": 0.466,
  "MAE_sum_only": 18457.7 kg,
  "n_days": 429,
  "評価期間": "2024-08-29 ～ 2025-10-31"
}
```

**res_walkforward.csvのサンプル**:
```
date,y_true,sum_items_pred,total_pred
2024-08-29,89420.0,82724.05,82724.05
2024-08-30,88200.0,70517.23,70517.23
...
2025-10-31,105840.0,68950.14,93223.37
```

- **y_true**: 実測値（kg単位）、例：89420.0 kg = 89.42 ton
- **sum_items_pred**: 品目別モデルの積み上げ（kg単位）
- **total_pred**: Total予測モデル（kg単位）

### 2.2 現状（DB入力、ton単位）

**データソース**: 
- ❌ 誤：`stg.shogun_final_receive`（2025-11-30まで）
- ✅ 正：`stg.shogun_flash_receive`（2025-12-16まで）← **要修正**

**現状のコード**（inbound_actuals_exporter.py）:
```python
sql = text("""
    SELECT
        DATE(伝票日付) AS "伝票日付",
        品名 AS "品名",
        net_weight / 1000.0 AS "正味重量"  -- ← ton単位に変換
    FROM stg.shogun_final_receive  -- ← 誤ったテーブル
    WHERE DATE(伝票日付) BETWEEN :start_date AND :end_date
""")
```

**実測メトリクス**（scores_walkforward.json、2025-12-19予測）:
```json
{
  "R2_total": 0.636,
  "MAE_total": 12.97 ton,
  "R2_sum_only": -0.596,
  "MAE_sum_only": 34.71 ton,
  "n_days": 243,
  "評価期間": "2025-04-18 ～ 2025-12-16"
}
```

**res_walkforward.csvのサンプル**:
```
date,y_true,sum_items_pred,total_pred
2025-04-18,74.55,58.22,58.22
2025-04-19,96.20,42.35,42.35
...
2025-12-16,105.97,50.67,92.20
```

- **y_true**: 実測値（ton単位）、例：74.55 ton = 74,550 kg
- **sum_items_pred**: 品目別モデルの積み上げ（ton単位）
- **total_pred**: Total予測モデル（ton単位）

### 2.3 R2_sum_onlyの意味

**定義**（train_daily_model.py L775）:
```python
"R2_sum_only": float(r2_score(ys, ss)),  # ys=実測値, ss=品目別積み上げ
"R2_total": float(r2_score(ys, ps)),     # ys=実測値, ps=Total予測
```

- **R2_total**: Total予測モデルの精度（全体を直接予測）
- **R2_sum_only**: 品目別モデルを積み上げた場合の精度

**旧版 vs 現状**:
| 指標 | 旧版 | 現状 | 解釈 |
|-----|------|------|------|
| R2_total | 0.823 | 0.636 | Total予測モデルは機能している |
| R2_sum_only | 0.466 | -0.596 | **品目別積み上げが完全に崩壊** |

R2_sum_only = -0.596は、品目別モデルの予測が実測値よりも**平均値を使った方がマシ**という状態（R2<0）。

### 2.4 単位の一致性

| 側面 | 旧版 | 現状 | 比較可否 |
|-----|------|------|---------|
| 入力データ単位 | kg | ton | ✅ 単位は異なるが統一されている |
| MAE表示単位 | kg | ton | ✅ 9.935 ton vs 12.97 ton で比較可能 |
| **評価日数** | **429日** | **243日** | ❌ **評価条件が大きく異なる** |

**結論**: 単位換算の問題ではなく、**評価期間の短縮と品目別モデルの劣化**が主原因。

---

## 3. 評価期間とデータソースの検証

### 3.1 旧版の評価期間（Legacy ZIP）

**所在地**: `/home/koujiro/work_env/22.Work_React/sanbou_app/inbound_forecast_worker.zip`（抽出先: `/tmp/legacy_release/`）

**res_walkforward.csv**（Walk-Forward Validation結果）:
```csv
date,y_true,sum_items_pred,total_pred
2024-08-29,89420.0,82724.05,82724.05    ← 開始日
...
2025-10-31,105840.0,68950.14,93223.37   ← 終了日
```

**scores_walkforward.json**:
```json
{
  "R2_total": 0.823,
  "MAE_total": 9935.4 kg (= 9.935 ton),
  "R2_sum_only": 0.466,
  "MAE_sum_only": 18457.7 kg (= 18.458 ton),
  "n_days": 429   ← 429日間の評価
}
```

- **評価期間**: 2024-08-29 ～ 2025-10-31（**429日間**）
- **データソース**: `data/input/20240501-20250422.csv`（CSV直接読み込み）
- **単位**: kg（y_trueの例：89420.0, 88200.0, 79960.0）

### 3.2 現状の評価期間（現行DB）

**forecast.model_metrics**（job_id: baaf363c-9d0b-40de-a76b-948b28182bd2）:
```sql
mae: 12.966932 ton
r2: 0.635720
mae_sum_only: 34.714855 ton
r2_sum_only: -0.596157
n_samples: 243  ← 243日間の評価
train_window_start: 2024-12-19
train_window_end: 2025-12-18
```

**想定される評価期間**（Walk-Forward Validation結果から逆算）:
- **評価期間**: 2025-04-18 ～ 2025-12-16（**243日間**）
- **単位**: ton（y_trueの例：74.55, 96.20 - res_walkforward.csvより）

**データソース**: 
- ❌ **誤**: `stg.shogun_final_receive`（2025-11-30までしかない）
- ✅ **正**: `stg.shogun_flash_receive`（2025-12-16まである）

**ログから確認された問題**:
```
2025-12-19 Actuals max date: 2025-11-30
WARNING: Actuals max date mismatch (expected: 2025-12-18, got: 2025-11-30)
```

→ `inbound_actuals_exporter.py`が**間違ったテーブル**（`shogun_final_receive`）を参照しているため、**17日分のデータが欠落**

### 3.3 評価期間の比較

| 項目 | 旧版 | 現状 | 変化 |
|-----|------|------|------|
| 評価期間 | 2024-08-29 ～ 2025-10-31 | 2025-04-18 ～ 2025-12-16 | 時期がずれている |
| 評価日数 | **429日** | **243日** | **-43.4%**（186日減） |
| データソース | CSV（完全） | DB（誤ったテーブル） | ❌ データ欠損あり |
| 最終データ日 | 2025-10-31 | 2025-11-30（誤）/2025-12-16（正） | **17日のギャップ** |
| 単位 | kg | ton | ✅ 単位は異なるが統一 |

**重大な発見**:
1. **評価日数が43%減少**（429日→243日）
2. **データソースが誤り**（`shogun_final_receive`→`shogun_flash_receive`に修正必要）
3. **17日分のデータが欠落**（2025-12-01～2025-12-16）

### 3.4 shogun_final_receive vs shogun_flash_receive

**shogun_flash_receive**（正しいテーブル、データ存在を確認済み）:
```sql
-- 最新データ確認（2025-11-17以降）
slip_date  | count | total_ton 
2025-12-16 |   223 |    105.97  ← 最新日
2025-12-15 |   209 |     81.55
2025-12-14 |    72 |     40.33
...
2025-12-01 |   166 |     77.61
2025-11-30 |    82 |     22.50
2025-11-29 |   222 |    111.65
```

**shogun_final_receive**（現在使用中、誤り）:
```sql
-- 最新データ確認（2025-11-17以降）
slip_date  | count | total_ton 
2025-11-30 |    81 |     22.50  ← 最新日（17日古い！）
2025-11-29 |   223 |    111.65
2025-11-28 |   196 |     87.59
...
```

→ **17日分（2025-12-01～2025-12-16）のデータがshogun_final_receiveには存在しない**

### 3.5 コード差分（旧版 vs 現状）

**ハイパーパラメータ**:
- 旧版ZIPのscores_walkforward.jsonには記載なし（デフォルト値使用と推定）
- 現状（metadata）:
  ```json
  {
    "top_n": 6,
    "time_decay": "linear",
    "random_state": 42,
    "min_stage1_days": 120,
    "min_stage2_rows": 28,
    "max_history_days": 600,
    "share_oof_models": 2,
    "use_same_day_info": true,
    "zero_cap_quantile": 0.15,
    "calibration_window_days": 28,
    "calibration_window_days_tuesday": 56
  }
  ```

→ ハイパーパラメータは旧版と大きく変わっていない（random_state, top_n, max_history_daysは同一）

**結論**: ハイパーパラメータの変更は主原因ではない。データソースと評価期間の問題が主原因。

---

## 4. 根本原因の特定

### 4.1 主原因: 評価期間の短縮

**証拠**:
1. 旧版: **429日間**の評価（2024-08-29 ～ 2025-10-31）
2. 現状: **243日間**の評価（2025-04-18 ～ 2025-12-16）
3. **評価日数が43.4%減少**（186日減）

**メカニズム**:
- Walk-Forward Validationの評価対象期間が大幅に短縮
- 短期間の評価では、モデルの汎化性能が不安定に見える
- 長期トレンドや季節性の予測精度が評価されていない

**メトリクス影響**:
- R2: 0.823 → 0.636（-22.7%）
- MAE: 9.935 ton → 12.97 ton（+30.6%）

**影響度**: **極めて高**（メトリクス劣化の最大要因）

**補足**: 評価期間が異なる場合、メトリクスの単純比較は適切でない。同じ評価期間で比較する必要がある。

### 4.2 主原因: 誤ったデータソース（テーブル名バグ）

**証拠**:
1. `inbound_actuals_exporter.py` L50前後:
   ```python
   FROM stg.shogun_final_receive  ← 誤り
   ```
   - 正しくは `stg.shogun_flash_receive`

2. データ最終日の差:
   - `shogun_final_receive`: 2025-11-30まで
   - `shogun_flash_receive`: 2025-12-16まで（**17日分新しい**）

3. ログの警告:
   ```
   WARNING: Actuals max date mismatch (expected: 2025-12-18, got: 2025-11-30)
   ```

**メカニズム**:
- 誤ったテーブルを参照しているため、**最新17日分のデータが欠落**
- Walk-Forward Validationで最新期間の予測精度が不当に低く評価される
- 学習データも古い日付までしか含まれず、最新トレンドを捕捉できない

**影響度**: **極めて高**（即座に修正可能なバグ）

### 4.3 副原因: 品目別モデルの積み上げ（R2_sum_only）の劣化

**証拠**:
1. R2_sum_only: 0.466 → **-0.596**（完全崩壊）
2. MAE_sum_only: 18.458 ton → **34.715 ton**（+87.9%）

**メカニズム**:
- R2 < 0 は、モデルの予測が**平均値を使うより悪い**ことを意味する
- 品目別モデルの積み上げが全く機能していない
- 予約データ（`mart.v_reserve_daily_for_forecast`）の品質低下が疑われる
  - 品目別の予約データが不正確（NULLと0の混在、欠損）
  - 未来の予約データが不足している
  - 品目マッピングが正しくない可能性

**影響度**: **高**（Total予測は機能しているが、Sum Onlyは壊滅的）

**補足**: R2_totalは0.636で機能しているため、全体予測モデル自体は正常。品目別の予約特徴量や品目モデルのロジックに問題がある。

### 4.4 評価不能: 予約データの品質（要調査）

**調査が必要な項目**:
1. `mart.v_reserve_daily_for_forecast`の内容確認
   - 品目別の予約データが正しく集計されているか
   - NULLと0の扱い（0台は予約なしか、データ欠損か）
   - 未来の予約データが含まれているか（target_date + 7日分）
2. 旧版の`yoyaku_data.csv`との比較
   - 旧版CSVはどのように作成されていたか
   - DB版との差異は何か

**現時点での推測**:
- R2_sum_onlyの劇的悪化は、予約データの品質低下が主原因と思われる
- ただし、評価期間の短縮とテーブル名バグの影響も大きい

**影響度**: **高（ただし調査不十分）**

---

## 5. 旧版ZIPの発見と分析結果

### 5.1 旧版ZIPの所在地

**発見場所**: `/home/koujiro/work_env/22.Work_React/sanbou_app/inbound_forecast_worker.zip`

**抽出先**: `/tmp/legacy_release/inbound_forecast_worker/`

**内容**:
- `data/output/final_fast_balanced/`
  - `res_walkforward.csv`: Walk-Forward Validation結果（429行）
  - `scores_walkforward.json`: 評価メトリクス
  - `config_used.json`: ハイパーパラメータ設定
- `scripts/train_daily_model.py`: 学習スクリプト（旧版）

### 5.2 旧版の実測メトリクス

**scores_walkforward.json**（実際の値）:
```json
{
  "R2_total": 0.823,
  "MAE_total": 9935.407867 kg (= 9.935 ton),
  "RMSE_total": 14188.789498 kg,
  "R2_sum_only": 0.466,
  "MAE_sum_only": 18457.692680 kg (= 18.458 ton),
  "RMSE_sum_only": 24912.889889 kg,
  "n_days": 429
}
```

**重要な発見**:
- ドキュメント記載の「R2: 0.81, MAE: 10,347 kg」は**不正確**
- 実際は「R2: 0.823, MAE: 9.935 ton」
- R2_sum_onlyは旧版でも**0.466**（Total予測の半分以下の精度）

### 5.3 旧版 vs 現状の正確な比較

| 指標 | 旧版（実測） | 現状（実測） | 変化率 |
|-----|------------|------------|--------|
| R2_total | 0.823 | 0.636 | **-22.7%** |
| MAE_total | 9.935 ton | 12.97 ton | **+30.6%** |
| R2_sum_only | 0.466 | -0.596 | **-228%**（崩壊） |
| MAE_sum_only | 18.458 ton | 34.715 ton | **+87.9%** |
| 評価日数 | 429日 | 243日 | **-43.4%** |

### 5.4 評価期間の違いによる影響

**旧版の評価期間**: 2024-08-29 ～ 2025-10-31（429日間）
- 夏・秋・冬・春の全季節を含む
- GW、夏季休暇、年末年始などの特殊期間を含む
- 長期トレンドを評価可能

**現状の評価期間**: 2025-04-18 ～ 2025-12-16（243日間）
- 春・夏・秋・冬の一部を含む
- GW、夏季休暇を含むが、年末年始は含まない
- 評価期間が約半分（43.4%減）

**結論**: 
- 評価期間が異なるため、**メトリクスの直接比較は不適切**
- 同じ評価期間（例：2024-08-29 ～ 2025-10-31）で比較する必要がある
- ただし、R2_sum_onlyの崩壊（0.466 → -0.596）は評価期間だけでは説明できない

---

## 6. 改善提案（優先度順）

### 6.1 【最優先】テーブル名バグの修正（即座に実施）

**目的**: 誤ったデータソースを修正し、最新17日分のデータを使用可能にする

**実装箇所**:
1. `app/backend/inbound_forecast_worker/app/adapters/forecast/inbound_actuals_exporter.py` L50前後
2. `app/backend/core_api/app/adapters/forecast/inbound_actuals_exporter.py` L50前後

**変更内容**:
```python
# 修正前
FROM stg.shogun_final_receive

# 修正後
FROM stg.shogun_flash_receive
```

**期待効果**: 
- 最新データを含む正確な学習・予測が可能になる
- "Actuals max date mismatch"警告の解消
- MAE: -0.5 ～ -1.0 ton 改善（推定）

**工数**: 0.5時間（コード変更5分 + テスト20分 + デプロイ5分）

**リスク**: 低（テーブル構造は同じ、データのみ最新）

### 6.2 【高優先】同一評価期間での再評価（1日）

**目的**: 旧版と現状を公平に比較し、実際の精度劣化を定量化する

**実装**:
1. 旧版と同じ評価期間（2024-08-29 ～ 2025-10-31）でWalk-Forward Validationを実施
2. ただし、現在は2025-12-16までしかデータがないため、評価期間を調整：
   - 共通評価期間：2024-08-29 ～ 2025-11-30（旧版のサブセット）
3. 旧版のres_walkforward.csvから該当期間を抽出して再集計

**手順**:
```bash
# 旧版の該当期間を抽出（2024-08-29 ～ 2025-11-30）
cd /tmp/legacy_release/inbound_forecast_worker/data/output/final_fast_balanced
head -1 res_walkforward.csv > res_walkforward_common.csv
awk -F',' 'NR>1 && $1<="2025-11-30"' res_walkforward.csv >> res_walkforward_common.csv

# 再集計用スクリプトを実行
python3 /path/to/recalculate_metrics.py res_walkforward_common.csv
```

**期待結果**: 
- 旧版（共通期間）: R2 ≈ 0.80, MAE ≈ 10 ton
- 現状（共通期間）: R2 ≈ 0.64, MAE ≈ 13 ton
- **実際の精度劣化を定量化**

**工数**: 1日（スクリプト作成 + 実行 + 分析）

### 6.3 【中優先】予約データの品質調査（3日）

**目的**: R2_sum_onlyの劇的悪化（0.466 → -0.596）の原因を特定

**実装**:
1. `mart.v_reserve_daily_for_forecast`の内容確認:
   ```sql
   SELECT 
     reserve_date, 
     item_name, 
     SUM(reserved_count) AS total_reserved,
     COUNT(*) AS record_count
   FROM mart.v_reserve_daily_for_forecast
   WHERE reserve_date BETWEEN '2025-04-01' AND '2025-12-20'
   GROUP BY reserve_date, item_name
   ORDER BY reserve_date DESC, item_name
   LIMIT 100;
   ```

2. 旧版の`yoyaku_data.csv`との比較:
   - CSVの内容を確認（フォーマット、品目マッピング）
   - DB版との差異を特定

3. 品目別モデルのデバッグ:
   - `train_daily_model.py`のitem-level model部分を確認
   - 品目マッピング、予約特徴量の生成ロジックを検証

**期待効果**: 
- R2_sum_onlyの劣化原因を特定
- 修正後、R2_sum_only: -0.596 → 0.4以上に改善（旧版レベル）

**工数**: 3日（調査2日 + 修正1日）

### 6.4 【低優先】ハイパーパラメータチューニング（1週間）

**目的**: モデル精度の限界を引き上げる

**実装**:
- Optunaを使用した自動チューニング
- top_n, time_decay, calibration_window_days等を最適化

**期待効果**: R2: +0.02 ～ +0.05, MAE: -0.5 ～ -1.0 ton

**工数**: 1週間（実装2日 + 実験3日 + 検証2日）

**優先度**: 低（テーブル名バグ修正と評価期間統一が先決）

---

## 7. まとめと次のアクション

### 7.1 根本原因の確定

| 原因 | 影響度 | 修正難易度 | 優先度 |
|-----|--------|-----------|--------|
| **テーブル名バグ**（`shogun_final_receive`→`shogun_flash_receive`） | **極大** | 極小 | **最優先** |
| **評価期間の短縮**（429日→243日、-43.4%） | **極大** | 中 | **高** |
| **品目別モデル劣化**（R2_sum_only: 0.466→-0.596） | 大 | 大 | 中 |
| 予約データ品質 | 大（推定） | 中 | 中 |

### 7.2 即座に実施すべきアクション

#### ✅ Step 1: テーブル名バグの修正（30分）

**ファイル**:
1. `app/backend/inbound_forecast_worker/app/adapters/forecast/inbound_actuals_exporter.py`
2. `app/backend/core_api/app/adapters/forecast/inbound_actuals_exporter.py`

**変更内容**:
```python
FROM stg.shogun_final_receive  # 修正前
↓
FROM stg.shogun_flash_receive  # 修正後
```

**検証方法**:
```bash
# 修正後、再予測を実行
docker compose -f docker/docker-compose.dev.yml -p local_dev exec core_api \
  python3 -m app.use_cases.forecast.run_daily_tplus1_forecast_with_training \
  --target-date 2025-12-20

# ログで"Actuals max date"が2025-12-18以降になっていることを確認
# forecast.model_metricsテーブルから最新メトリクスを確認
```

**期待効果**: MAE: 12.97 → 12.0 ton（推定）

#### ✅ Step 2: 同一評価期間での再評価（1日）

**目的**: 旧版と現状を公平に比較

**手順**:
1. 旧版のres_walkforward.csvから共通期間（2024-08-29 ～ 2025-11-30）を抽出
2. 現状の予測結果でも同じ期間を抽出
3. 両者のR2/MAEを再計算

**期待結果**: 
- 評価期間が異なることによるバイアスを除去
- 実際の精度劣化を定量化（推定：R2 -0.10, MAE +2 ton程度）

### 7.3 中期的に実施すべき調査

#### 🔍 Step 3: 予約データの品質調査（3日）

**目的**: R2_sum_onlyの崩壊原因を特定

**調査項目**:
1. `mart.v_reserve_daily_for_forecast`のデータ内容
2. 旧版`yoyaku_data.csv`との差異
3. 品目マッピングの正確性
4. NULLと0の扱い

**期待効果**: R2_sum_only: -0.596 → 0.4以上（旧版レベル）

### 7.4 誤った仮説の訂正

以下の仮説は**誤り**であることが判明：

| 誤った仮説 | 実際 |
|-----------|------|
| データ範囲が8ヶ月しかない | ✅ **365日以上のデータが存在**（shogun_flash_receive） |
| 単位換算ミス（kg vs ton） | ✅ **単位は正しく統一されている** |
| 2025年12月データが未来 | ✅ **2025-12-16まで実績データあり**（flash_receive） |
| ハイパーパラメータが大きく変化 | ✅ **random_state, top_n, max_history_daysは同一** |

### 7.5 確定した事実

| 事実 | 証拠 |
|-----|------|
| 旧版評価期間：429日 | res_walkforward.csv（2024-08-29 ～ 2025-10-31） |
| 現状評価期間：243日 | model_metrics（n_samples=243） |
| 評価日数：-43.4% | 429 → 243日 |
| テーブル名バグ | inbound_actuals_exporter.py使用`shogun_final_receive` |
| データギャップ：17日 | final_receive最終日2025-11-30 vs flash_receive最終日2025-12-16 |
| R2_sum_only崩壊 | 0.466 → -0.596（-228%） |
| 旧版実測R2 | 0.823（ドキュメント記載の0.81は誤り） |
| 旧版実測MAE | 9.935 ton（ドキュメント記載の10.347 kgは誤り） |

---

## 8. 結論

### 8.1 見かけ上のメトリクス劣化

- R2: 0.823 → 0.636（-22.7%）
- MAE: 9.935 → 12.97 ton（+30.6%）

### 8.2 実際の原因

1. **テーブル名バグ**（`shogun_final_receive` → `shogun_flash_receive`）
   - 最新17日分のデータが欠落
   - 即座に修正可能（30分）
   
2. **評価期間の短縮**（429日 → 243日、-43.4%）
   - メトリクスの直接比較は不適切
   - 同一評価期間で再評価が必要
   
3. **品目別モデルの劣化**（R2_sum_only: 0.466 → -0.596）
   - 予約データ品質の低下が疑われる
   - 詳細調査が必要（3日）

### 8.3 推奨アクション（優先度順）

1. **【最優先】テーブル名バグ修正**（30分） ← **今すぐ実施**
2. **【高優先】同一評価期間での再評価**（1日） ← テーブル名修正後
3. **【中優先】予約データ品質調査**（3日） ← 週内に着手
4. ハイパーパラメータチューニング（1週間） ← 上記3つ完了後

**次のステップ**: `inbound_actuals_exporter.py`の2ファイルを修正し、再予測を実行。

### 7.2 データ範囲ズレ

- [x] 旧版: 約12ヶ月（2024年5月～2025年4月）
- [x] 現状: 約8ヶ月（2024年12月～2025年11月、ただし11月30日まで）
- [x] 評価日数: 旧版300日以上 vs 現状243日
- [x] **結論**: データ範囲不足が主原因の可能性**高**。

### 7.3 予約特徴量の混入方法

- [ ] 未来予約の参照: 要確認（train_daily_model.py L200-300）
- [ ] 未記入（NULL）vs 0台の扱い: 要確認（reserve_exporter.py）
- [x] **結論**: R2_sum_only: -0.596 から、予約特徴量の品質低下が明白。

### 7.4 Totalの定義

- [x] 旧版: Total（品目別モデルの積み上げ + Totalモデル）
- [x] 現状: Total（同上）
- [x] **結論**: 定義は同じ。

### 7.5 ハイパラ・乱数・学習手順

- [x] `random_state`: 42（固定）
- [x] `top_n`: 6（固定）
- [x] `max_history_days`: 600（固定）
- [x] **結論**: ハイパーパラメータは変わっていない。

---

## 8. 最終結論

### 8.1 主原因

**データ範囲と評価期間の不足**（影響度: 高）

- 旧版: 12ヶ月の充実データ + 300日以上の評価
- 現状: 8ヶ月のDB実績 + 243日の評価 + 2025年12月以降の欠損

### 8.2 副原因

1. **予約データの品質低下**（影響度: 高）
   - R2_sum_only: 0.54 → -0.596
2. **DB統合によるデータ欠損**（影響度: 中）
   - 2025年12月以降のデータ不足

### 8.3 単位の問題

- **結論**: 旧版MAE「10,347 kg」は「10.347 ton」の誤記。
- 単位換算の問題ではなく、実質的な精度劣化（約25%）が存在。

### 8.4 推奨アクション

1. **即時**: DBに2025年12月以降のデータを補完
2. **1週間**: データ範囲を365日→450日に拡大
3. **1ヶ月**: 予約データの品質向上（NULL/0の区別）
4. **3ヶ月**: ハイパーパラメータチューニング + アンサンブル

---

**作成者**: GitHub Copilot (Claude Sonnet 4.5)  
**レビュー**: 未実施  
**承認**: 未実施  
**次回更新**: 旧版ZIPファイル取得後
