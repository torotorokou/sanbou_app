# 予測区間命名変更・移行計画

**作成日**: 2025-12-18  
**目的**: p10/p90の命名を統計的に正確にし、誤解を防ぐ  
**調査**: [forecast_interval_semantics_investigation.md](./forecast_interval_semantics_investigation.md)

---

## 🎯 移行ゴール

1. **命名の正確性**: σ由来の値を "sigma" 系命名にする
2. **後方互換性**: 既存データ・クエリを壊さない
3. **段階的移行**: 3フェーズで安全に切り替え

---

## 📊 新命名案

### 採用案（推奨）

| 現在 | 新命名 | 意味 | 根拠 |
|------|--------|------|------|
| `p50` | `median` | 中央値（50%分位点） | Quantile回帰 alpha=0.5 |
| `p10` | `lower_1sigma` | median - 1.28σ | σ逆算（正規分布仮定） |
| `p90` | `upper_quantile_90` | 90%分位点 | Quantile回帰 alpha=0.9 |

### 代替案

| 案 | lower | median | upper | 特徴 |
|----|-------|--------|-------|------|
| **A（推奨）** | `lower_1sigma` | `median` | `upper_quantile_90` | 正確・明示的 |
| **B** | `lower_bound` | `median` | `upper_bound` | シンプル・意味は曖昧 |
| **C** | `q10_approx` | `q50` | `q90` | 短い・approximateを明示 |

**最終決定**: **案A**を採用
- 計算方法が明確
- 統計的に正確
- 長いが誤解を招かない

---

## 🔄 移行戦略（3フェーズ）

### Phase 1: カラム追加・互換維持（即座実施）

**期間**: 1-2週間  
**目標**: 新カラムを追加し、旧カラムも維持

#### 1-1. DBマイグレーション

```sql
-- forecast.daily_forecast_results
ALTER TABLE forecast.daily_forecast_results 
  ADD COLUMN median numeric(10, 3) NULL,
  ADD COLUMN lower_1sigma numeric(10, 3) NULL,
  ADD COLUMN upper_quantile_90 numeric(10, 3) NULL;

-- コメント追加
COMMENT ON COLUMN forecast.daily_forecast_results.median IS '中央値（50%分位点、Quantile回帰）';
COMMENT ON COLUMN forecast.daily_forecast_results.lower_1sigma IS '下限（median - 1.28σ、正規分布仮定）';
COMMENT ON COLUMN forecast.daily_forecast_results.upper_quantile_90 IS '上限（90%分位点、Quantile回帰）';

-- 既存データの移行（安全に）
UPDATE forecast.daily_forecast_results
SET 
  median = p50,
  lower_1sigma = p10,
  upper_quantile_90 = p90
WHERE median IS NULL;
```

#### 1-2. コード修正（保存側）

**ファイル**: `run_daily_tplus1_forecast_with_training.py`

```python
# 新カラムと旧カラムの両方を保存
result = DailyForecastResult(
    job_id=job_id,
    target_date=target_date,
    # 新カラム（優先）
    median=p50,
    lower_1sigma=p10,
    upper_quantile_90=p90,
    # 旧カラム（互換維持、Phase 3で削除）
    p50=p50,
    p10=p10,
    p90=p90,
    unit="ton",
    generated_at=datetime.now(timezone.utc)
)
```

#### 1-3. ドキュメント更新

- DBスキーマコメント
- API仕様書に新フィールド追加
- README/開発ガイドに移行計画を記載

---

### Phase 2: 読み出し側を新カラム優先（2週間後）

**期間**: 2-4週間  
**目標**: 新カラムを優先使用、旧カラムはフォールバック

#### 2-1. コード修正（読み出し側）

**ファイル**: API/UIのレスポンス生成箇所

```python
# 新カラム優先、旧カラムはフォールバック
def get_forecast_result(row):
    return {
        "target_date": row.target_date,
        "median": row.median or row.p50,  # 新優先
        "lower_1sigma": row.lower_1sigma or row.p10,
        "upper_quantile_90": row.upper_quantile_90 or row.p90,
        # 互換性のため旧フィールドも返す（Phase 3で削除）
        "p50": row.median or row.p50,
        "p10": row.lower_1sigma or row.p10,
        "p90": row.upper_quantile_90 or row.p90,
    }
```

#### 2-2. フロントエンド更新

- グラフ・テーブルの表示を新フィールド使用
- ラベル変更: "P10/P90" → "下限（-1σ）/ 上限（90%点）"

---

### Phase 3: 旧カラム廃止（4-6週間後）

**期間**: 移行完了後1ヶ月  
**目標**: p10/p50/p90カラムを削除

**条件**:
- ✅ すべてのクライアントが新APIに移行
- ✅ 旧カラムへのアクセスがログに記録されていない
- ✅ データ移行が完全に完了

#### 3-1. 旧カラム削除

```sql
-- 警告: 実行前に全クライアント移行確認
ALTER TABLE forecast.daily_forecast_results 
  DROP COLUMN p10,
  DROP COLUMN p50,
  DROP COLUMN p90;
```

#### 3-2. コード cleanup

- 旧カラム参照をすべて削除
- フォールバックロジックを削除

---

## 🛡️ 安全策

### ロールバック計画

**Phase 1中にロールバック**:
```sql
-- 新カラム削除だけ（旧カラムは無傷）
ALTER TABLE forecast.daily_forecast_results 
  DROP COLUMN median,
  DROP COLUMN lower_1sigma,
  DROP COLUMN upper_quantile_90;
```

**Phase 2中にロールバック**:
- コードを戻す（旧カラム優先に）
- DBはそのまま（両方のカラムが存在）

### データ整合性チェック

```sql
-- 新旧カラムの差分チェック
SELECT 
  COUNT(*) AS total_rows,
  COUNT(CASE WHEN ABS(median - p50) > 0.01 THEN 1 END) AS median_mismatch,
  COUNT(CASE WHEN ABS(lower_1sigma - p10) > 0.01 THEN 1 END) AS lower_mismatch,
  COUNT(CASE WHEN ABS(upper_quantile_90 - p90) > 0.01 THEN 1 END) AS upper_mismatch
FROM forecast.daily_forecast_results;
```

期待結果: すべて0（差分なし）

---

## 📅 タイムライン

| フェーズ | 期間 | 主なタスク | 完了条件 |
|---------|------|----------|---------|
| **Phase 1** | Week 1-2 | DBマイグレーション、保存側修正 | 新カラムへの保存開始 |
| **Phase 2** | Week 3-6 | 読み出し側修正、UI更新 | 新カラム優先使用 |
| **移行期間** | Week 7-10 | モニタリング、旧カラム使用状況確認 | 旧カラムアクセス0 |
| **Phase 3** | Week 11+ | 旧カラム削除 | 移行完了 |

---

## 🔍 影響範囲チェックリスト

### データベース

- [x] forecast.daily_forecast_results（主テーブル）
- [ ] 他の予測結果テーブル（weekly, monthly等）
- [ ] Viewがp10/p50/p90を参照している箇所

### コード

- [x] run_daily_tplus1_forecast_with_training.py（保存処理）
- [ ] API レスポンス（読み出し処理）
- [ ] UI コンポーネント（グラフ・テーブル）
- [ ] レポート生成（CSV出力等）

### ドキュメント

- [x] 調査レポート
- [x] 移行計画
- [ ] API仕様書
- [ ] ユーザーガイド

### テスト

- [ ] 保存処理のユニットテスト
- [ ] API統合テスト
- [ ] UIスナップショットテスト

---

## 📝 コミュニケーション計画

### ステークホルダー通知

**対象**:
- データ分析チーム
- フロントエンド開発チーム
- API利用チーム
- プロダクトオーナー

**内容**:
1. **Phase 1開始前**: 移行計画の共有（このドキュメント）
2. **Phase 1完了時**: 新カラム利用可能の通知
3. **Phase 2移行前**: 旧カラム非推奨の告知（Deprecated）
4. **Phase 3実施前**: 削除予定日の最終通知

---

## 🎓 学習ポイント

### なぜこの命名が必要か

1. **統計的正確性**: p10は10%分位点ではなく、σ由来
2. **誤解の防止**: 分位点とσは異なる概念
3. **保守性向上**: 計算方法が名前から分かる

### 将来の改善案

1. **p10モデルの学習**: Quantile回帰で alpha=0.1 を追加
2. **非対称区間**: 上限と下限で異なる信頼度を設定
3. **動的区間**: データ分布に応じて区間を調整

---

**策定日**: 2025-12-18  
**承認**: （レビュー後記入）  
**実施責任者**: （担当者記入）
