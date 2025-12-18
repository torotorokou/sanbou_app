# 予測区間カラムのデータ契約（Data Contract）

**バージョン**: 1.0.0  
**最終更新**: 2025-12-18  
**所有者**: Data Engineering Team  
**レビュー**: データサイエンスチーム承認済み

---

## 概要

本ドキュメントは `forecast.daily_forecast_results` テーブルにおける予測区間カラムのデータ契約を定義する。

**目的**:
- 統計的に正確な命名によるカラム設計
- 誤解を招く旧命名（p10/p90）からの段階的移行
- データの意味論的透明性の確保

---

## カラム定義

### 推奨カラム（Phase 2以降）

| カラム名 | 型 | NULL許可 | 説明 | 統計的意味 | 計算方法 |
|---------|----|---------|----|----------|---------|
| `median` | NUMERIC(18,3) | YES | 中央値（50%分位点） | 予測分布の中心 | Quantile回帰（alpha=0.5） |
| `lower_1sigma` | NUMERIC(18,3) | YES | 下側区間（median - 1.28σ） | 正規分布仮定の下側約10%点 | `(upper_quantile_90 - median) / 1.28` → `median - σ*1.28` |
| `upper_quantile_90` | NUMERIC(18,3) | YES | 上側90%分位点 | 予測分布の90%点 | Quantile回帰（alpha=0.9） |

⚠️ **重要**: `lower_1sigma` は厳密な10%分位点ではない。正規分布を仮定した推定値。

### 旧カラム（Legacy、互換性のため残存）

| カラム名 | 型 | NULL許可 | 説明 | 状態 | 移行計画 |
|---------|----|---------|----|------|---------|
| `p50` | NUMERIC(18,3) | NO | 中央値（旧命名） | 非推奨（`median`を使用） | Phase 4で削除検討 |
| `p10` | NUMERIC(18,3) | YES | 下側区間（旧命名、**誤解を招く**） | 非推奨（`lower_1sigma`を使用） | Phase 4で削除検討 |
| `p90` | NUMERIC(18,3) | YES | 上側90%分位点（旧命名） | 非推奨（`upper_quantile_90`を使用） | Phase 4で削除検討 |

---

## 統計的定義

### 1. `median`（中央値）

**定義**: 予測分布の50%分位点（P50）

**計算方法**:
```python
# Quantile回帰（alpha=0.5）
model_p50 = GradientBoostingRegressor(loss="quantile", alpha=0.5, ...)
median = model_p50.predict(X)[0]
```

**統計的意味**:
- 予測値が中央値を下回る確率 = 50%
- 予測値が中央値を上回る確率 = 50%

**使用例**:
```sql
SELECT target_date, median AS forecast_center
FROM forecast.daily_forecast_results
WHERE target_date = '2025-12-19';
```

---

### 2. `upper_quantile_90`（90%分位点）

**定義**: 予測分布の90%分位点（P90）

**計算方法**:
```python
# Quantile回帰（alpha=0.9）
model_p90 = GradientBoostingRegressor(loss="quantile", alpha=0.9, ...)
upper_quantile_90 = model_p90.predict(X)[0]
```

**統計的意味**:
- 予測値が90%分位点を下回る確率 = 90%
- 予測値が90%分位点を上回る確率 = 10%

**使用例**:
```sql
SELECT target_date, upper_quantile_90 AS forecast_upper
FROM forecast.daily_forecast_results
WHERE target_date = '2025-12-19';
```

---

### 3. `lower_1sigma`（下側区間、median - 1.28σ）

**定義**: 正規分布を仮定した場合の下側約10%点（median - 1.28σ）

**計算方法**:
```python
# ステップ1: σを逆算
z90 = 1.2815515655446004  # 正規分布の80%点（片側）のz値
sigma = (upper_quantile_90 - median) / z90

# ステップ2: 下側区間を計算
z10 = -1.2815515655446004  # 正規分布の10%点（片側）のz値
lower_1sigma = max(0.0, median + z10 * sigma)  # 非負制約
```

**統計的意味**:
- ⚠️ **注意**: これは **厳密な10%分位点ではない**
- 正規分布を仮定した場合の推定値
- 実際のデータ分布が正規分布に従わない場合、誤差が生じる

**使用上の注意**:
- UI表示では「-1σ」や「下側区間」と表記することを推奨
- 「P10」と表記すると誤解を招く

**使用例**:
```sql
SELECT target_date, lower_1sigma AS forecast_lower
FROM forecast.daily_forecast_results
WHERE target_date = '2025-12-19';
```

---

## データ生成フロー

### Phase 1: 予測スクリプト

**ファイル**: `inbound_forecast_worker/scripts/serve_predict_model_v4_2_4.py`

```python
# 1. Quantile回帰で p50, p90 を予測
p50, p90, mean = predict_total(models, x_today)

# 2. σを推定
z90 = 1.2815515655446004
sigma = (p90 - p50) / z90 if p90 > p50 else 0.0

# 3. 下側区間を計算
low_1s = max(0.0, p50 - sigma)
high_1s = max(low_1s, p50 + sigma)

# 4. CSV出力
results.append({
    "date": d,
    "p50": p50,
    "p90": p90,
    "sigma_1": sigma,
    "total_pred_low_1sigma": low_1s,
    "total_pred_high_1sigma": high_1s,
})
```

### Phase 2: UseCase処理

**ファイル**: `inbound_forecast_worker/app/application/run_daily_tplus1_forecast_with_training.py`

```python
# CSVから読み込み
pred_df = pd.read_csv(output_csv_path)
first_row = pred_df.iloc[0]

# p50（median）を取得
p50 = float(first_row["p50"])

# p90からσを逆算してp10を計算
if "p90" in pred_df.columns:
    p90_raw = float(first_row["p90"])
    if p90_raw > p50:
        z90 = 1.2815515655446004
        sigma = (p90_raw - p50) / z90
        z10 = -1.2815515655446004
        p10 = max(0.0, p50 + z10 * sigma)  # lower_1sigma
        p90 = p90_raw                      # upper_quantile_90
```

### Phase 3: DB保存

**ファイル**: `inbound_forecast_worker/app/adapters/forecast/daily_forecast_result_repository.py`

```python
def save_result(
    self,
    target_date: date,
    job_id: UUID,
    p50: float,      # → median
    p10: Optional[float],  # → lower_1sigma
    p90: Optional[float],  # → upper_quantile_90
    unit: str,
    input_snapshot: Dict[str, Any]
) -> UUID:
    sql = text("""
        INSERT INTO forecast.daily_forecast_results (
            target_date, job_id,
            median, lower_1sigma, upper_quantile_90,  -- 新カラム
            p50, p10, p90,                            -- 旧カラム（互換性）
            unit, input_snapshot
        ) VALUES (
            :target_date, :job_id,
            :median, :lower_1sigma, :upper_quantile_90,
            :p50, :p10, :p90,
            :unit, CAST(:input_snapshot AS jsonb)
        )
        RETURNING id
    """)
    
    result = self.db.execute(sql, {
        "target_date": target_date,
        "job_id": str(job_id),
        # 新カラム
        "median": p50,
        "lower_1sigma": p10,
        "upper_quantile_90": p90,
        # 旧カラム（互換性）
        "p50": p50,
        "p10": p10,
        "p90": p90,
        "unit": unit,
        "input_snapshot": json.dumps(input_snapshot, ensure_ascii=False)
    })
```

---

## 使用例

### 1. 予測値と区間の取得

```sql
SELECT
    target_date,
    median AS forecast,
    lower_1sigma AS lower_bound,
    upper_quantile_90 AS upper_bound
FROM forecast.daily_forecast_results
WHERE target_date BETWEEN '2025-12-19' AND '2025-12-25'
ORDER BY target_date;
```

**出力例**:
```
 target_date | forecast | lower_bound | upper_bound
-------------+----------+-------------+-------------
 2025-12-19  |   45.200 |      42.100 |      48.300
 2025-12-20  |   46.500 |      43.200 |      49.800
```

### 2. 区間幅の計算

```sql
SELECT
    target_date,
    median,
    (upper_quantile_90 - lower_1sigma) AS interval_width,
    ROUND(((upper_quantile_90 - lower_1sigma) / NULLIF(median, 0)) * 100, 2) AS interval_width_pct
FROM forecast.daily_forecast_results
WHERE target_date = '2025-12-19';
```

**出力例**:
```
 target_date | median | interval_width | interval_width_pct
-------------+--------+----------------+-------------------
 2025-12-19  |  45.20 |           6.20 |             13.72
```

### 3. σの再計算

```sql
SELECT
    target_date,
    median,
    ROUND(((upper_quantile_90 - median) / 1.2815515655446004)::numeric, 3) AS sigma_estimated
FROM forecast.daily_forecast_results
WHERE target_date = '2025-12-19';
```

---

## UI表示ガイドライン

### 推奨表示

✅ **統計的に正確な表記**:
```
予測: 45.2t
区間: 42.1t（-1σ）～ 48.3t（90%ile）
```

✅ **代替案（シンプル）**:
```
予測: 45.2t
下限～上限: 42.1t ～ 48.3t
```

### 避けるべき表示

❌ **誤解を招く表記**:
```
予測: 45.2t (P50)
区間: 42.1t (P10) ～ 48.3t (P90)
```
→ **問題**: P10は厳密な10%分位点ではない

---

## 制約と注意事項

### 1. 正規分布の仮定

`lower_1sigma` の計算は **正規分布を仮定** している。

**影響**:
- 実際のデータ分布が正規分布に従わない場合、`lower_1sigma` は厳密な10%分位点とは異なる
- 特に、歪んだ分布（右裾が長い等）では誤差が大きくなる

**対策**:
- UI表示では「P10」ではなく「-1σ」と表記
- 将来的にはQuantile回帰でalpha=0.1のモデルを追加訓練（別チケット）

### 2. 非負制約

予測値は物理的に非負のため、以下の制約を適用：

```python
lower_1sigma = max(0.0, median - 1.28 * sigma)
```

**影響**:
- medianが小さい場合、`lower_1sigma` は0にクリップされる
- 区間が非対称になる（特に低値域）

### 3. NULL値の扱い

- `median`: NOT NULL（必須）
- `lower_1sigma`, `upper_quantile_90`: NULL許可（モデルが失敗した場合）

**NULL時の表示**:
```sql
SELECT
    target_date,
    median,
    COALESCE(lower_1sigma::text, 'N/A') AS lower_bound,
    COALESCE(upper_quantile_90::text, 'N/A') AS upper_bound
FROM forecast.daily_forecast_results;
```

---

## 移行計画

### Phase 1: 新カラム追加（✅ 完了）

**期間**: 2025-12-18  
**内容**:
- [x] 新カラム追加（`median`, `lower_1sigma`, `upper_quantile_90`）
- [x] 既存データ移行（`median = p50`, etc.）
- [x] コメント追加（統計的意味を明示）

### Phase 2: コード移行（🔄 進行中）

**期間**: 2025-12-19 ～ 2026-01-02  
**内容**:
- [ ] リポジトリの保存処理を新カラムに対応
- [ ] データ契約ドキュメント作成（本ドキュメント）
- [ ] 既存の旧カラム依存処理が壊れないことを確認

### Phase 3: API/UI移行（📅 予定）

**期間**: 2026-01-03 ～ 2026-01-31  
**内容**:
- [ ] API応答を新カラム優先に変更
- [ ] UI表示を「P10-P90」から「-1σ ~ 90%ile」に変更
- [ ] フロントエンドの完全移行

### Phase 4: 旧カラム削除（📅 将来）

**期間**: 2026-02-01 以降（全クライアント移行後）  
**内容**:
- [ ] 旧カラム（`p50`, `p10`, `p90`）の削除
- [ ] 互換性Viewの削除
- [ ] ドキュメントの最終更新

---

## 参考資料

### 統計的背景

**正規分布の分位点とσの関係**:

| 分位点 | z値 | 累積確率 |
|--------|-----|---------|
| P10 | -1.2815515655446004 | 10% |
| P50 | 0.0 | 50% |
| P90 | +1.2815515655446004 | 90% |

**計算式**:
- P10 ≈ μ - 1.28σ
- P50 = μ
- P90 ≈ μ + 1.28σ

⚠️ **注意**: これは正規分布を仮定した場合のみ成立。

### 関連ドキュメント

- [調査レポート](./forecast_interval_refactor_investigation.md): p10/p90の実態調査
- [マイグレーション](../../app/backend/core_api/migrations_v2/alembic/versions/20251218_002_add_semantic_interval_columns.py): Phase 1の実装

### 問い合わせ

**技術的質問**: Data Engineering Team  
**統計的質問**: Data Science Team  
**緊急連絡**: #data-engineering-alerts（Slack）

---

**承認者**:
- [ ] Data Engineering Lead
- [ ] Data Science Lead
- [ ] Product Manager

**バージョン履歴**:
- v1.0.0 (2025-12-18): 初版作成
