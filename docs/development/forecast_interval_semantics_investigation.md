# 予測区間の意味調査レポート（p10/p90 vs σ）

**調査日**: 2025-12-18  
**調査者**: GitHub Copilot  
**目的**: forecast.daily_forecast_results の p10/p90 が分位点かσ由来かを証拠付きで判定

---

## 🎯 結論

**判定: 混在（Quantile回帰 + σ変換）**

- **CSV生成側**: p50とp90は**Quantile回帰**（分位点）として計算される
- **DB保存側**: p10は**σ逆算**により生成される（p90からz値で逆算）
- **フォールバック**: total_pred_low_1sigma / total_pred_high_1sigma（mean±σ）を使用

### 命名の問題点

1. **p10**: DB保存時に計算される値で、実際は「p50 - 1.28σ」（分位点ではない）
2. **p90**: Quantile回帰の90%分位点（正しい）
3. **混乱**: p10とp90が異なるロジックで生成されているため誤解を招く

---

## 📊 証拠：コード調査結果

### 1. モデル学習（train_daily_model.py）

**場所**: [train_daily_model.py#L485-L490](../../../app/backend/inbound_forecast_worker/scripts/train_daily_model.py#L485-L490)

```python
gbdt_p50 = GradientBoostingRegressor(
    loss="quantile", alpha=0.5,  # ← 50%分位点
    n_estimators=args.gbr_n_estimators, learning_rate=0.05,
    max_depth=3, subsample=0.9, random_state=cfg.random_state)
gbdt_p90 = GradientBoostingRegressor(
    loss="quantile", alpha=0.9,  # ← 90%分位点
    n_estimators=max(args.gbr_n_estimators, 200), learning_rate=0.05,
    max_depth=3, subsample=0.9, random_state=cfg.random_state)
```

**証拠**: 
- `loss="quantile"` を使用
- `alpha=0.5` → p50（中央値）
- `alpha=0.9` → p90（90%分位点）
- ✅ **p50とp90はQuantile回帰による分位点**

---

### 2. σの計算（serve_predict_model_v4_2_4.py）

**場所**: [serve_predict_model_v4_2_4.py#L1212-L1219](../../../app/backend/inbound_forecast_worker/scripts/serve_predict_model_v4_2_4.py#L1212-L1219)

```python
# 1シグマ推定（優先: 分位点 -> 代替: 残差の頑健標準偏差）
z90 = 1.2815515655446004  # 90%分位点のz値（正規分布）
sigma_q = (p90 - p50) / z90 if (np.isfinite(p90) and np.isfinite(p50) and (p90 > p50)) else float("nan")
sigma_hist_dow = resid_std_by_dow_cur.get(dow, float("nan"))
sigma = sigma_q if np.isfinite(sigma_q) else (sigma_hist_dow if np.isfinite(sigma_hist_dow) else (resid_std_all_cur if np.isfinite(resid_std_all_cur) else 0.0))
sigma = float(max(0.0, sigma))
low_1s = max(0.0, total_pred_today - sigma)   # mean - 1σ
high_1s = max(low_1s, total_pred_today + sigma)  # mean + 1σ
```

**証拠**:
- p90とp50の差からσを逆算: `sigma = (p90 - p50) / z90`
- z90 = 1.2816（正規分布の80%分位点のz値）
- CSV出力: `total_pred_low_1sigma` と `total_pred_high_1sigma`
- ✅ **σは分位点から逆算されている**

---

### 3. DB保存時の変換（run_daily_tplus1_forecast_with_training.py）

**場所**: [run_daily_tplus1_forecast_with_training.py#L238-L265](../../../app/backend/inbound_forecast_worker/app/application/run_daily_tplus1_forecast_with_training.py#L238-L265)

```python
# p10/p90も取得（存在する場合）
# 注意: CSV列は異なる意味を持つ
#   - "p50", "p90": quantile回帰による50%/90%分位点
#   - "total_pred_low_1sigma", "total_pred_high_1sigma": total_pred ± 1σ
# DBには本来のquantile値を保存すべき
p10 = None
p90 = None

# quantile回帰の値を優先使用
if "p50" in pred_df.columns and "p90" in pred_df.columns:
    # p90からσを逆算してp10を推定 (p90 = p50 + 1.28σ と仮定)
    p90_raw = float(first_row["p90"])
    if p90_raw > p50:
        z90 = 1.2815515655446004  # 80%分位点のz値
        sigma = (p90_raw - p50) / z90
        z10 = -1.2815515655446004  # 20%分位点のz値
        p10 = max(0.0, p50 + z10 * sigma)  # ← p50 - 1.28σ
        p90 = p90_raw
    else:
        # p90がp50以下の場合 (zero_cap等でキャップされた場合)
        # σベースの値を使用
        if "total_pred_low_1sigma" in pred_df.columns and "total_pred_high_1sigma" in pred_df.columns:
            p10 = float(first_row["total_pred_low_1sigma"])
            p90 = float(first_row["total_pred_high_1sigma"])
elif "total_pred_low_1sigma" in pred_df.columns and "total_pred_high_1sigma" in pred_df.columns:
    # quantile値がない場合はσベースの値を使用（互換性のため）
    p10 = float(first_row["total_pred_low_1sigma"])
    p90 = float(first_row["total_pred_high_1sigma"])
```

**証拠**:
- p10はCSVに存在しない（学習時にp10モデルは作られていない）
- DB保存時に `p10 = p50 + z10 * sigma` で計算（z10 = -1.2816）
- 計算式: `p10 = p50 - 1.28σ`
- ⚠️ **p10は分位点ではなく、p50からσを使って逆算した値**

---

## 🔍 問題の詳細分析

### CSV出力の列定義

| 列名 | 意味 | 計算方法 |
|------|------|---------|
| `p50` | 50%分位点 | Quantile回帰（alpha=0.5） |
| `p90` | 90%分位点 | Quantile回帰（alpha=0.9） |
| `total_pred_low_1sigma` | mean - 1σ | mean_pred - sigma |
| `total_pred_high_1sigma` | mean + 1σ | mean_pred + sigma |
| `sigma_1` | 推定σ | (p90 - p50) / 1.2816 |

**注意**: p10はCSVに含まれていない

### DB保存時の変換

| DBカラム | 値の由来 | 実際の意味 |
|---------|---------|-----------|
| `p50` | CSV `p50` | ✅ 50%分位点（正しい） |
| `p10` | **計算**: `p50 - 1.28σ` | ⚠️ σ由来（誤解を招く命名） |
| `p90` | CSV `p90` | ✅ 90%分位点（正しい） |

---

## 📈 統計的解釈

### Quantile回帰の意味

- **p50**: データの中央値（50%点）
- **p90**: データの上位90%点
- **非対称**: p50 - p10 ≠ p90 - p50（データ分布次第）

### σ（標準偏差）の意味

- **正規分布を仮定**: mean ± 1σ = 約68%信頼区間
- **z値を使った変換**:
  - z90 = 1.2816 → 90%分位点（正規分布）
  - z10 = -1.2816 → 10%分位点（正規分布）
- **対称**: mean - 1σ と mean + 1σ は mean から等距離

### 現在の実装の問題

1. **p90は分位点** → データ分布に忠実
2. **p10はσ由来** → 正規分布を仮定（実データは非正規の可能性）
3. **混在による混乱** → p10とp90が異なるロジックで生成

---

## 🎓 なぜこの実装になったか？

### 推測される設計意図

1. **p90モデルのみ学習**:
   - リソース削減（モデル数を減らす）
   - p90（上限予測）が業務上重要

2. **p10は逆算で代用**:
   - p10モデルを学習しないコスト削減
   - 正規分布仮定でσから推定
   - コメント: "DBには本来のquantile値を保存すべき"（コード内警告あり）

3. **フォールバック（σ直接使用）**:
   - p90がzero_cap等で潰れた場合
   - `total_pred_low_1sigma` / `total_pred_high_1sigma` を使用

---

## ⚠️ 命名の問題点

### 誤解を招く点

| 現在の命名 | 実際の意味 | 誤解 |
|-----------|-----------|------|
| `p10` | p50 - 1.28σ | 「10%分位点」と誤解 |
| `p90` | 90%分位点 | ✅ 正しい |

### 統計的妥当性

- **p90**: ✅ Quantile回帰により推定、データ分布に忠実
- **p10**: ⚠️ 正規分布仮定でσから逆算、実データが非正規なら不正確

### ドキュメント不足

- コード内のコメント以外に説明がない
- DBユーザーやAPI利用者が誤解する可能性

---

## 🔄 推奨される対応

### Option 1: 命名を正確にする（推奨）

**変更案**:
- `p10` → `lower_1sigma` または `p50_minus_1sigma`
- `p90` → `p90_quantile` または `upper_quantile`（現状維持でも可）
- `p50` → `p50_quantile`（現状維持でも可）

**理由**:
- σ由来であることを明示
- 分位点との混同を防ぐ
- 統計的に正確な命名

### Option 2: p10モデルを学習する（理想だが高コスト）

**変更案**:
- Quantile回帰で alpha=0.1 のモデルを追加学習
- p10を真の10%分位点として算出

**課題**:
- 学習コスト増加
- モデル数増加（p50, p10, p90, mean の4モデル）
- 過去データとの整合性

### Option 3: ドキュメント整備のみ（最小限対応）

**変更案**:
- DBスキーマコメントに計算式を記載
- API仕様書に意味を明記
- コード内コメントを充実

**課題**:
- 命名の誤解は残る
- 長期的には混乱の元

---

## 📋 次のアクションアイテム

### 短期（必須）

1. ✅ **調査完了**: p10/p90の意味を証拠付きで確定
2. 🔲 **ドキュメント作成**: forecast_interval_semantics.md
3. 🔲 **移行計画策定**: 後方互換を保ちつつ命名変更

### 中期（推奨）

1. 🔲 **DB移行**: 新カラム追加（lower_1sigma, upper_1sigma）
2. 🔲 **コード修正**: 保存・読み出し処理を新カラム対応
3. 🔲 **API更新**: レスポンスに新フィールド追加

### 長期（検討）

1. 🔲 **旧カラム廃止**: p10/p90カラムの削除
2. 🔲 **p10モデル学習**: 真の10%分位点モデル追加（要検討）

---

## 📎 関連ファイル

- **学習**: [train_daily_model.py](../../../app/backend/inbound_forecast_worker/scripts/train_daily_model.py#L485-L516)
- **予測**: [serve_predict_model_v4_2_4.py](../../../app/backend/inbound_forecast_worker/scripts/serve_predict_model_v4_2_4.py#L1210-L1240)
- **保存**: [run_daily_tplus1_forecast_with_training.py](../../../app/backend/inbound_forecast_worker/app/application/run_daily_tplus1_forecast_with_training.py#L238-L275)
- **DBスキーマ**: [20251218_001_add_daily_forecast_results_table.py](../../../app/backend/core_api/migrations_v2/alembic/versions/20251218_001_add_daily_forecast_results_table.py)

---

**調査完了日**: 2025-12-18  
**判定**: p10はσ由来、p90はQuantile分位点（混在）  
**推奨**: 命名を lower_1sigma / upper_quantile に変更し、誤解を防ぐ
