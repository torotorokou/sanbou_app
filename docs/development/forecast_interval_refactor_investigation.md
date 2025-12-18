# 予測区間カラムのリファクタリング調査レポート

**調査日**: 2025-12-18  
**調査者**: AI Assistant  
**目的**: p10/p90カラムの実態を調査し、適切なカラム設計への移行方針を策定

---

## エグゼクティブサマリー

### 結論
現状の `p10/p90` カラムは **意味論的に誤解を招く命名** であり、以下の問題がある：

- **p50**: ✅ Quantile回帰（alpha=0.5）による50%分位点 → **正しい命名**
- **p90**: ✅ Quantile回帰（alpha=0.9）による90%分位点 → **正しい命名**
- **p10**: ❌ **分位点ではない** → p50からσを逆算して計算（`p50 - 1.28σ`、正規分布仮定）→ **誤解を招く命名**

### 推奨アクション
**Option A（推奨）**: 新カラム追加による意味論的命名の導入
- `median`: p50（50%分位点）
- `sigma`: 標準偏差（p90とp50から逆算）
- `lower_1sigma`: median - 1.28σ（下側区間）
- `upper_quantile_90`: 90%分位点（p90）

p25/p75は **現状では生成不可能**（分布サンプルが保存されていない）ため、将来対応とする。

---

## 1. 現状調査：p10/p90の生成方法

### 1.1 予測スクリプト：serve_predict_model_v4_2_4.py

**場所**: [serve_predict_model_v4_2_4.py#L215-L231](../../../app/backend/inbound_forecast_worker/scripts/serve_predict_model_v4_2_4.py#L215-L231)

```python
def predict_total(models: Dict, x_today_raw: pd.DataFrame) -> Tuple[float,float,float]:
    """
    Total予測（p50, p90, mean）
    """
    m_p50 = models.get("p50") or models.get("gbdt_p50")  # Quantile回帰 alpha=0.5
    m_p90 = models.get("p90") or models.get("gbdt_p90")  # Quantile回帰 alpha=0.9
    m_ls = models.get("ls") or models.get("mean")        # 最小二乗法（mean）

    # Predict with available models
    mean = float(m_ls.predict(Xt)[0]) if m_ls is not None else float("nan")
    p50 = float(m_p50.predict(Xt)[0]) if m_p50 is not None else mean
    p90 = float(m_p90.predict(Xt)[0]) if m_p90 is not None else mean
    return p50, p90, mean
```

**証拠**:
- `p50`: `GradientBoostingRegressor(loss="quantile", alpha=0.5)` → **50%分位点**
- `p90`: `GradientBoostingRegressor(loss="quantile", alpha=0.9)` → **90%分位点**

### 1.2 σ（標準偏差）の計算

**場所**: [serve_predict_model_v4_2_4.py#L1213-L1219](../../../app/backend/inbound_forecast_worker/scripts/serve_predict_model_v4_2_4.py#L1213-L1219)

```python
# 1シグマ推定（優先: 分位点 -> 代替: 残差の頑健標準偏差）
z90 = 1.2815515655446004  # 正規分布の80%分位点のz値（片側）
sigma_q = (p90 - p50) / z90 if (np.isfinite(p90) and np.isfinite(p50) and (p90 > p50)) else float("nan")
sigma_hist_dow = resid_std_by_dow_cur.get(dow, float("nan"))  # 曜日別残差標準偏差
sigma = sigma_q if np.isfinite(sigma_q) else (sigma_hist_dow if np.isfinite(sigma_hist_dow) else (resid_std_all_cur if np.isfinite(resid_std_all_cur) else 0.0))
sigma = float(max(0.0, sigma))
low_1s = max(0.0, total_pred_today - sigma)    # median - 1σ
high_1s = max(low_1s, total_pred_today + sigma) # median + 1σ
```

**CSV出力**:
```python
results.append({
    "date": d,
    "p50": p50,                          # Quantile alpha=0.5
    "p90": p90,                          # Quantile alpha=0.9
    "sigma_1": sigma,                    # (p90 - p50) / 1.28
    "total_pred_low_1sigma": low_1s,     # p50 - sigma
    "total_pred_high_1sigma": high_1s,   # p50 + sigma
})
```

### 1.3 p10の計算（DB保存時）

**場所**: [run_daily_tplus1_forecast_with_training.py#L243-L256](../../../app/backend/inbound_forecast_worker/app/application/run_daily_tplus1_forecast_with_training.py#L243-L256)

```python
# quantile回帰の値を優先使用
if "p50" in pred_df.columns and "p90" in pred_df.columns:
    # p90からσを逆算してp10を推定 (p90 = p50 + 1.28σ と仮定)
    p90_raw = float(first_row["p90"])
    if p90_raw > p50:
        z90 = 1.2815515655446004  # 80%分位点のz値
        sigma = (p90_raw - p50) / z90
        z10 = -1.2815515655446004  # 20%分位点のz値
        p10 = max(0.0, p50 + z10 * sigma)  # ← ここで計算される！
        p90 = p90_raw
    else:
        # フォールバック: total_pred_low_1sigma を使用
        if "total_pred_low_1sigma" in pred_df.columns:
            p10 = float(first_row["total_pred_low_1sigma"])
```

**証拠**: p10は **計算値**であり、Quantile回帰の出力ではない。

---

## 2. 問題点の整理

### 2.1 命名の誤解

| カラム名 | 実際の意味 | 誤解される意味 | 問題 |
|---------|----------|-------------|------|
| `p50` | 50%分位点（Quantile回帰） | 50%分位点 | ✅ 正しい |
| `p90` | 90%分位点（Quantile回帰） | 90%分位点 | ✅ 正しい |
| `p10` | **p50 - 1.28σ（正規分布仮定）** | 10%分位点 | ❌ **誤解を招く** |

### 2.2 統計的妥当性

**p10の計算式**:
```python
sigma = (p90 - p50) / 1.2815515655446004
p10 = p50 - 1.2815515655446004 * sigma
```

**問題**:
1. **正規分布を仮定**している（実際のデータ分布が正規とは限らない）
2. **p10という命名**が「10%分位点」を示唆するが、実際は「median - 1.28σ」
3. 統計的には「下側±1σ区間」を「p10」と呼ぶのは不適切

### 2.3 p25/p75は生成可能か？

**結論**: ❌ **現状では不可能**

**理由**:
1. 予測スクリプトは **分位点モデル（p50, p90）** のみを訓練
2. **分布サンプル**（bootstrapの予測値配列など）は保存されていない
3. p25/p75を生成するには：
   - Option A: Quantile回帰でalpha=0.25, 0.75のモデルを追加訓練
   - Option B: Bootstrapサンプルを保存し、事後的に分位点を計算

**推奨**: 当面はOption A（sigma追加）に寄せ、p25/p75は別チケットで対応

---

## 3. 既存マイグレーションの確認

### 3.1 テーブル作成マイグレーション

**場所**: [20251218_001_add_daily_forecast_results_table.py](../../../app/backend/core_api/migrations_v2/alembic/versions/20251218_001_add_daily_forecast_results_table.py)

```sql
CREATE TABLE forecast.daily_forecast_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_date DATE NOT NULL,
    job_id UUID NOT NULL,
    p50 NUMERIC(18,3) NOT NULL,
    p10 NUMERIC(18,3) NULL,
    p90 NUMERIC(18,3) NULL,
    unit TEXT NOT NULL DEFAULT 'ton',
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    input_snapshot JSONB NOT NULL DEFAULT '{}'
);
```

### 3.2 意味論的カラム追加マイグレーション（既存）

**場所**: [20251218_002_add_semantic_interval_columns.py](../../../app/backend/core_api/migrations_v2/alembic/versions/20251218_002_add_semantic_interval_columns.py)

**内容**:
- ✅ 新カラム追加済み: `median`, `lower_1sigma`, `upper_quantile_90`
- ✅ 既存データ移行済み（`median = p50`, `lower_1sigma = p10`, `upper_quantile_90 = p90`）
- ✅ コメントで統計的意味を明示

**状態**: **Phase 1（新カラム追加）は完了済み**

---

## 4. 推奨方針

### 4.1 短期方針（今回のリファクタリング）

**目標**: p10/p90の誤解を解消し、意味論的に正確なカラムに移行

**実施内容**:
1. ✅ **Phase 1（完了済み）**: 新カラム追加（`median`, `lower_1sigma`, `upper_quantile_90`）
2. **Phase 2（次回）**: コード修正
   - リポジトリの保存処理を新カラムに対応（旧カラムは互換のため併記）
   - データ契約ドキュメント作成
3. **Phase 3（将来）**: API/UI読み出しを新カラム優先に変更
4. **Phase 4（遠い将来）**: 旧カラム削除（全クライアント移行後）

### 4.2 中期方針（p25/p75対応）

**前提**: 現状では分布サンプルが無いため、p25/p75は生成不可能

**実施内容**:
1. **別チケットで対応**（このリファクタリングには含めない）
2. 選択肢：
   - Option A: Quantile回帰でalpha=0.25, 0.75のモデルを追加訓練
   - Option B: Bootstrap予測を実装し、分布サンプルを保存

### 4.3 統計的推奨事項

**現状の区間表現（推奨）**:
- **中心**: `median`（50%分位点、Quantile回帰）
- **上側**: `upper_quantile_90`（90%分位点、Quantile回帰）
- **下側**: `lower_1sigma`（median - 1.28σ、正規分布仮定）
  - ⚠️ **注意**: これは厳密な10%分位点ではない

**UI表示推奨**:
```
予測: 45.2t
区間: 42.1t（-1σ）～ 48.3t（90%ile）
```

**避けるべき表示**:
```
予測: 45.2t (P50)
区間: 42.1t (P10) ～ 48.3t (P90)  ← P10は誤解を招く！
```

---

## 5. データ契約

### 5.1 新カラムの定義

| カラム | 型 | 意味 | 計算方法 | 統計的根拠 |
|--------|----|----|---------|----------|
| `median` | NUMERIC(18,3) | 中央値（50%分位点） | Quantile回帰（alpha=0.5） | 分位点 |
| `lower_1sigma` | NUMERIC(18,3) | 下側区間（median - 1.28σ） | (p90 - median) / 1.28 → median - σ*1.28 | 正規分布仮定（±1σ） |
| `upper_quantile_90` | NUMERIC(18,3) | 上側90%分位点 | Quantile回帰（alpha=0.9） | 分位点 |
| `sigma` | NUMERIC(18,3) | 標準偏差（推定） | (upper_quantile_90 - median) / 1.28 | 正規分布仮定 |

### 5.2 旧カラムの扱い（legacy）

| カラム | 状態 | 移行計画 |
|--------|------|---------|
| `p50` | 互換のため残存 | Phase 3以降で削除検討 |
| `p10` | 互換のため残存（非推奨） | Phase 3以降で削除検討 |
| `p90` | 互換のため残存 | Phase 3以降で削除検討 |

---

## 6. 受け入れ条件

### 6.1 必須条件

- [x] 新カラム（`median`, `lower_1sigma`, `upper_quantile_90`）がDBに存在する
- [x] 既存データが新カラムに移行されている
- [ ] リポジトリの保存処理が新カラムに対応している
- [ ] データ契約ドキュメントが作成されている
- [ ] 既存の旧カラム依存処理が壊れていない

### 6.2 将来対応

- [ ] UI/APIが新カラムを優先的に使用（Phase 3）
- [ ] 旧カラム削除（Phase 4、全クライアント移行後）
- [ ] p25/p75対応（別チケット、分布サンプル実装後）

---

## 7. 参考資料

### 7.1 関連ファイル

- [serve_predict_model_v4_2_4.py](../../../app/backend/inbound_forecast_worker/scripts/serve_predict_model_v4_2_4.py): 予測スクリプト（p50/p90生成）
- [run_daily_tplus1_forecast_with_training.py](../../../app/backend/inbound_forecast_worker/app/application/run_daily_tplus1_forecast_with_training.py): p10計算ロジック
- [daily_forecast_result_repository.py](../../../app/backend/inbound_forecast_worker/app/adapters/forecast/daily_forecast_result_repository.py): DB保存処理
- [20251218_002_add_semantic_interval_columns.py](../../../app/backend/core_api/migrations_v2/alembic/versions/20251218_002_add_semantic_interval_columns.py): マイグレーション

### 7.2 統計的背景

**正規分布の分位点とσの関係**:
- P10（10%分位点）≈ mean - 1.28σ
- P50（50%分位点）= mean
- P90（90%分位点）≈ mean + 1.28σ

⚠️ **注意**: これは **正規分布を仮定** した場合のみ成立。実際のデータが正規分布に従わない場合、この関係は成立しない。

### 7.3 z値の参考値

| 分位点 | z値（片側） | 累積確率 |
|--------|-----------|---------|
| P10 | -1.2815515655446004 | 10% |
| P50 | 0.0 | 50% |
| P90 | +1.2815515655446004 | 90% |

---

## 8. アクションアイテム

### 優先度: 高

1. [ ] データ契約ドキュメント作成（`forecast_interval_data_contract.md`）
2. [ ] リポジトリ保存処理の修正（新カラム対応）
3. [ ] 既存データの整合性確認（新旧カラムの値が一致するか）

### 優先度: 中

4. [ ] API/UIの読み出し処理を新カラム優先に変更（Phase 3）
5. [ ] フロントエンドの表示を「P10-P90」から「-1σ ~ 90%ile」に変更

### 優先度: 低（将来対応）

6. [ ] p25/p75対応の別チケット作成
7. [ ] 旧カラム削除の計画策定（Phase 4）

---

**調査完了日**: 2025-12-18  
**次回レビュー日**: Phase 2完了後
