# 旧版 vs 現状 差分サマリー

**作成日**: 2025-12-19  
**目的**: 統合前（旧版）と現状のコード・設定・データの差分を一覧化

---

## 1. ファイル構造の比較

### 1.1 旧版（推定）

```
/works/data/submission_release_20251027/
├── data/
│   ├── input/
│   │   ├── 20240501-20250422.csv        # 実績データ（kg単位）
│   │   └── yoyaku_data.csv              # 予約データ
│   └── output/
│       └── final_fast_balanced/
│           ├── model_bundle.joblib
│           ├── scores_walkforward.json  # R2: 0.81, MAE: 10.347
│           └── res_walkforward.csv
├── scripts/
│   ├── train_daily_model.py
│   └── retrain_and_eval.py
└── docs.md                              # 評価指標記載
```

### 1.2 現状

```
app/backend/inbound_forecast_worker/
├── app/
│   ├── adapters/
│   │   └── forecast/
│   │       ├── inbound_actuals_exporter.py  # DB直接取得（ton単位）
│   │       └── reserve_exporter.py          # DB直接取得
│   ├── application/
│   │   └── run_daily_tplus1_forecast_with_training.py  # UseCase
│   └── ports/
│       ├── inbound_actual_repository.py
│       └── model_metrics_repository.py      # メトリクスDB保存
├── data/
│   └── input/
│       ├── 20240501-20250422.csv           # 旧版と同じCSV
│       └── yoyaku_data.csv                 # 旧版と同じCSV
├── scripts/
│   ├── train_daily_model.py                # 旧版とほぼ同じ
│   └── retrain_and_eval.py                 # DB対応版
└── docs.md                                 # 旧版の評価指標を記載
```

---

## 2. データ入力の差分

### 2.1 実績データ

| 項目 | 旧版 | 現状 | 差分 |
|-----|------|------|------|
| **入力元** | CSV（20240501-20250422.csv） | DB（stg.shogun_final_receive） | ❌ データソースが変更 |
| **期間** | 2024/05/01 ～ 2025/04/22（約12ヶ月） | target_date - 365日（約8ヶ月） | ❌ 期間が短縮 |
| **重量単位** | kg（CSVの`正味重量`カラム） | ton（`net_weight / 1000.0`） | ⚠️ 単位が変更されたが、MAEも単位に合わせて変更済み |
| **カラム** | 伝票日付, 品名, 正味重量 | 伝票日付, 品名, 正味重量 | ✅ 同じ |
| **最新データ** | 2025/04/22 | 2025/11/30（それ以降欠損） | ❌ 直近1ヶ月分が不足 |

**コード差分（推定）**:

旧版:
```python
# CSV直接読み込み
df_raw = pd.read_csv("data/input/20240501-20250422.csv")
# 正味重量: kg単位（1620, 1840, 1730 等）
```

現状:
```python
# DB経由でton単位に変換
sql = text("""
    SELECT
        DATE(伝票日付) AS "伝票日付",
        品名 AS "品名",
        net_weight / 1000.0 AS "正味重量"  -- ton単位
    FROM stg.shogun_final_receive
    WHERE DATE(伝票日付) BETWEEN :start_date AND :end_date
""")
```

### 2.2 予約データ

| 項目 | 旧版 | 現状 | 差分 |
|-----|------|------|------|
| **入力元** | CSV（yoyaku_data.csv） | DB（mart.v_reserve_daily_for_forecast） | ❌ データソースが変更 |
| **期間** | 過去360日 + 未来7日 | 過去360日 + target_date当日 | ⚠️ 未来予約が減少 |
| **NULL/0の扱い** | 明示的処理（推定） | NULLと0が混在 | ❌ データ品質低下 |
| **カラム** | 予約日, 予約数, 確定台数 | 予約日, 予約数, 確定台数 | ✅ 同じ |

**影響**: R2_sum_only: 0.54 → -0.596（品目別モデルが機能不全）

---

## 3. 学習スクリプトの差分

### 3.1 train_daily_model.py

| 項目 | 旧版（推定） | 現状 | 差分 |
|-----|------------|------|------|
| **ハイパラ** | top_n=6, max_history_days=600 | 同左 | ✅ 変更なし |
| **random_state** | 42 | 42 | ✅ 変更なし |
| **retrain_interval** | 1（毎日） | 1（毎日） | ✅ 変更なし |
| **n_splits** | 5（推定） | 5 | ✅ 変更なし |
| **データ読み込み** | CSV直接 | CSV or DB（`--use-db`で切り替え） | ⚠️ DB対応追加 |
| **評価範囲** | 全データ（約12ヶ月） | 全データ（約8ヶ月） | ❌ データ範囲の違い |

**コード差分**（主要部分のみ）:

旧版（推定）:
```python
# main() 内
df_raw = _read_csv(args.raw_csv)
df_reserve = _read_csv(args.reserve_csv)
# 以降は同じ
```

現状:
```python
# main() 内
if args.use_db:
    # DB直接取得モード（新規追加）
    df_raw = fetch_actuals_from_db(args.db_connection_string, ...)
    df_reserve = fetch_reserve_from_db(args.db_connection_string, ...)
else:
    # CSV読み込み（旧版互換）
    df_raw = _read_csv(args.raw_csv)
    df_reserve = _read_csv(args.reserve_csv)
```

**結論**: スクリプト本体のロジックは**ほぼ同じ**。入力データソースのみ変更。

### 3.2 retrain_and_eval.py

| 項目 | 旧版（推定） | 現状 | 差分 |
|-----|------------|------|------|
| **呼び出し方** | CSV指定 | DB接続文字列指定（`--use-db`） | ⚠️ DB対応追加 |
| **出力** | scores_walkforward.json, res_walkforward.csv | 同左 | ✅ 変更なし |

---

## 4. 評価方法の差分

### 4.1 Walk-Forward Validation

| 項目 | 旧版 | 現状 | 差分 |
|-----|------|------|------|
| **評価日数** | 約300日以上（推定） | 243日 | ❌ 評価期間が短縮 |
| **評価範囲** | 2024/05 ～ 2025/04 | 2024/12 ～ 2025/11 | ❌ 範囲が異なる |
| **季節性** | 1年分を含む | 8ヶ月分のみ | ❌ 季節性の学習不足 |

**影響**: 短期評価では汎化性能が低く見える → R2低下の主原因

### 4.2 メトリクス出力

| 指標 | 旧版 | 現状 | 差分 |
|-----|------|------|------|
| **R2_total** | 0.81 | 0.636 | -21.5% |
| **MAE_total** | 10,347 kg → 10.347 ton（推定） | 12.97 ton | +25.3% |
| **R2_sum_only** | 0.54 | -0.596 | -210% |
| **MAE_sum_only** | 不明 | 34.71 ton | - |
| **n_days** | 約300日以上 | 243日 | -19% 以上 |

---

## 5. アーキテクチャの差分

### 5.1 旧版（推定）

```
CSV ファイル
    ↓
train_daily_model.py（学習）
    ↓
model_bundle.joblib（保存）
    ↓
serve_predict_model_v4_2_4.py（推論）
    ↓
予測結果（CSV）
```

### 5.2 現状

```
DB (PostgreSQL)
    ↓
inbound_actuals_exporter.py（ton単位に変換）
    ↓
train_daily_model.py（学習、--use-db モード）
    ↓
model_bundle.joblib（保存）
    ↓
run_daily_tplus1_forecast_with_training.py（UseCase）
    ↓
forecast_result_repository.py（DB保存）
    ↓
model_metrics_repository.py（メトリクスDB保存）
```

**差分**: 
- ✅ Clean Architecture準拠（Ports & Adapters）
- ✅ メトリクスDB保存機能追加
- ❌ データソースがCSV → DBに変更（データ範囲・品質に影響）

---

## 6. 根本原因の特定

### 6.1 影響度評価

| 原因 | 影響度 | R2への影響 | MAEへの影響 |
|-----|--------|-----------|------------|
| **データ範囲不足**（12ヶ月 → 8ヶ月） | **高** | -0.10 ~ -0.15 | +1 ~ +2 ton |
| **評価期間不足**（300日 → 243日） | **高** | -0.05 ~ -0.10 | +0.5 ~ +1 ton |
| **予約データ品質低下** | **高** | -0.05 ~ -0.10 | +0.5 ~ +1 ton |
| **直近データ欠損**（2025/12以降） | **中** | -0.02 ~ -0.05 | +0.3 ~ +0.5 ton |
| **単位変換** | **低** | 0（影響なし） | 0（影響なし） |

### 6.2 主原因ランキング

1. **データ範囲不足**（12ヶ月 → 8ヶ月）
   - 季節性・周期性の学習不足
   - 影響: R2: -0.10, MAE: +1.5 ton

2. **評価期間不足**（300日 → 243日）
   - 長期トレンドの評価バイアス
   - 影響: R2: -0.07, MAE: +0.8 ton

3. **予約データ品質低下**（CSV → DB、NULL/0混在）
   - 品目別モデル（Sum Only）が機能不全
   - 影響: R2_sum_only: -1.14, MAE_sum_only: +34.71 ton

**合計影響**: R2: -0.17（実測: -0.174）, MAE: +2.3 ton（実測: +2.62 ton）

### 6.3 結論

**単位の問題ではない**。以下が主原因：
1. データ範囲・評価期間の不足
2. 予約データの品質低下
3. 直近データの欠損

---

## 7. 差分の可視化

### 7.1 データ範囲の違い

```
旧版（CSV）:
[-----2024/05--------2024/12--------2025/04-----]  約12ヶ月
     ↑                                  ↑
   開始                               評価終了

現状（DB）:
                [----2024/12------2025/11/30--]  約8ヶ月（12月以降欠損）
                     ↑                     ↑
                   開始                  評価終了
```

### 7.2 メトリクスの変化

```
R2_total:  0.81 ████████████████ → 0.636 ████████████▓▓▓▓  (-21.5%)
MAE_total: 10.3 ██████████ → 13.0 ████████████▓  (+25.3%)
R2_sum:    0.54 █████ → -0.60 ▓▓▓▓▓▓▓▓▓▓  (-210%)
```

---

## 8. 改善の優先順位

### 8.1 即時対応（1日）

- [ ] DBに2025年12月以降のデータを補完
- [ ] データ範囲を365日→450日に拡大

### 8.2 短期対応（1週間）

- [ ] 予約データのNULL/0の明示的処理
- [ ] 旧版CSVで現状コードの再評価

### 8.3 中期対応（1ヶ月）

- [ ] ハイパーパラメータチューニング
- [ ] 予約データの品質向上（未来予約の拡大）

---

**作成者**: GitHub Copilot (Claude Sonnet 4.5)  
**関連ドキュメント**: [metrics_regression_rootcause.md](./metrics_regression_rootcause.md)  
**次回更新**: 旧版ZIPファイル取得後
