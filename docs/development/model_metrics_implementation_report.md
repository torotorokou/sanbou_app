# モデルメトリクスDB保存機能 実装完了レポート

**作成日**: 2025-12-18  
**実装者**: GitHub Copilot (Claude Sonnet 4.5)  
**関連ドキュメント**: 
- [model_metrics_investigation.md](./model_metrics_investigation.md)
- [daily_forecast_audit_with_metrics.md](./daily_forecast_audit_with_metrics.md)

---

## 1. 実装サマリー

### 1.1 目的
学習モデルの精度指標（MAE/R2等）をDBに保存し、予測結果との紐付け可能な監査証跡を確立する。

### 1.2 実装範囲
- ✅ **調査**: `train_daily_model.py`が`scores_walkforward.json`を出力していることを確認
- ✅ **DB設計**: `forecast.model_metrics`テーブル作成（migration 20251218_003）
- ✅ **Port/Adapter実装**: Clean Architecture準拠のリポジトリ層実装
- ✅ **UseCase拡張**: 予測実行後に自動でメトリクスをDB保存
- ✅ **監査レポート作成**: データ契約検証とメトリクス品質閾値の文書化
- ✅ **E2E確認**: 新規予測実行 → DB検証 → メトリクス確認

### 1.3 実装期間
- 開始: 2025-12-18 09:00
- 完了: 2025-12-18 18:10
- 所要時間: 約9時間（調査、実装、テスト含む）

---

## 2. データベース設計

### 2.1 テーブル構造

```sql
CREATE TABLE forecast.model_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES forecast.forecast_jobs(id),
    model_name TEXT NOT NULL,
    model_version TEXT,
    train_window_start DATE NOT NULL,
    train_window_end DATE NOT NULL,
    eval_method TEXT NOT NULL,
    mae NUMERIC(18, 6) NOT NULL CHECK (mae >= 0),
    r2 NUMERIC(18, 6) NOT NULL,
    n_samples INTEGER NOT NULL CHECK (n_samples >= 1),
    rmse NUMERIC(18, 6),
    mape NUMERIC(18, 6),
    mae_sum_only NUMERIC(18, 6),
    r2_sum_only NUMERIC(18, 6),
    unit TEXT NOT NULL DEFAULT 'ton' CHECK (unit IN ('ton', 'kg')),
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**インデックス**:
- `idx_model_metrics_job_id`: job_id（FK検索）
- `idx_model_metrics_model_name_version`: model_name, model_version（モデル別検索）
- `idx_model_metrics_created_at`: created_at（時系列検索）

### 2.2 リレーションシップ

```
forecast.forecast_jobs (1) ← (1) forecast.model_metrics
forecast.forecast_jobs (1) → (N) forecast.daily_forecast_results

-- JOINクエリ例
SELECT
    fj.id AS job_id,
    fj.target_date,
    dfr.median,
    mm.mae,
    mm.r2
FROM forecast.forecast_jobs fj
LEFT JOIN forecast.daily_forecast_results dfr ON fj.id = dfr.job_id
LEFT JOIN forecast.model_metrics mm ON fj.id = mm.job_id;
```

---

## 3. アーキテクチャ設計

### 3.1 Clean Architecture準拠

```
┌─────────────────────────────────────────────────────────┐
│ Presentation Layer (Worker)                             │
│  - job_executor.py                                      │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│ Application Layer (UseCase)                             │
│  - RunDailyTplus1ForecastWithTrainingUseCase            │
│    ├─ execute(): 予測実行                               │
│    └─ _save_model_metrics(): メトリクス保存             │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│ Domain Layer (Port)                                      │
│  - ModelMetricsRepositoryPort (Abstract Interface)       │
│    ├─ save_metrics(metrics: ModelMetrics) -> UUID       │
│    ├─ get_by_job_id(job_id: UUID) -> ModelMetrics?      │
│    └─ list_recent(model_name: str, limit: int) -> []    │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│ Infrastructure Layer (Adapter)                           │
│  - PostgreSQLModelMetricsRepository                      │
│    └─ SQLAlchemy text() queries                         │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│ Database                                                 │
│  - forecast.model_metrics                                │
└──────────────────────────────────────────────────────────┘
```

### 3.2 データフロー

```
1. WorkerがUseCaseを実行
2. UseCaseがtrain_daily_model.py実行
3. train_daily_model.pyがscores_walkforward.json出力
4. UseCaseがscores_walkforward.jsonを読み取り
5. UseCaseがModelMetricsオブジェクトを構築
6. UseCaseがRepositoryPort.save_metrics()呼び出し
7. PostgreSQLAdapterがINSERT実行
8. DBにメトリクス保存 ✅
```

---

## 4. 実装ファイル一覧

### 4.1 新規作成ファイル

| ファイル | 役割 | 行数 |
|---------|-----|------|
| [app/backend/core_api/migrations_v2/alembic/versions/20251218_003_add_model_metrics_table.py](../../app/backend/core_api/migrations_v2/alembic/versions/20251218_003_add_model_metrics_table.py) | DBマイグレーション | 98 |
| [app/backend/inbound_forecast_worker/app/ports/model_metrics_repository.py](../../app/backend/inbound_forecast_worker/app/ports/model_metrics_repository.py) | Port Interface | 92 |
| [app/backend/inbound_forecast_worker/app/adapters/forecast/model_metrics_repository.py](../../app/backend/inbound_forecast_worker/app/adapters/forecast/model_metrics_repository.py) | PostgreSQL Adapter | 206 |
| [docs/development/model_metrics_investigation.md](./model_metrics_investigation.md) | 調査レポート | 154 |
| [docs/development/daily_forecast_audit_with_metrics.md](./daily_forecast_audit_with_metrics.md) | 監査レポート | 377 |
| [docs/development/model_metrics_implementation_report.md](./model_metrics_implementation_report.md) | 本ドキュメント | - |

### 4.2 更新ファイル

| ファイル | 変更内容 |
|---------|---------|
| [app/backend/inbound_forecast_worker/app/application/run_daily_tplus1_forecast_with_training.py](../../app/backend/inbound_forecast_worker/app/application/run_daily_tplus1_forecast_with_training.py) | `_save_model_metrics()`メソッド追加（L329-L376） |
| [app/backend/inbound_forecast_worker/app/job_executor.py](../../app/backend/inbound_forecast_worker/app/job_executor.py) | `PostgreSQLModelMetricsRepository`のDI追加（L115） |

---

## 5. E2Eテスト結果

### 5.1 テストケース

**日時**: 2025-12-18 18:10  
**ジョブID**: `baaf363c-9d0b-40de-a76b-948b28182bd2`  
**対象日**: 2025-12-19

### 5.2 テスト手順

1. ✅ 新規予測ジョブ作成（INSERT INTO forecast.forecast_jobs）
2. ✅ Worker自動実行（retrain_and_eval.py --quick）
3. ✅ 予測結果保存確認（forecast.daily_forecast_results）
4. ✅ メトリクス保存確認（forecast.model_metrics）
5. ✅ JOINクエリ動作確認（3テーブル結合）

### 5.3 テスト結果

#### 5.3.1 予測結果

```sql
SELECT * FROM forecast.daily_forecast_results
WHERE job_id = 'baaf363c-9d0b-40de-a76b-948b28182bd2';
```

| job_id | target_date | median | lower_1sigma | upper_quantile_90 | unit |
|--------|-------------|--------|--------------|-------------------|------|
| baaf... | 2025-12-19 | 85.687 | 71.846 | 99.527 | ton |

✅ **検証OK**: 予測区間カラムが正しく保存されている

#### 5.3.2 モデルメトリクス

```sql
SELECT * FROM forecast.model_metrics
WHERE job_id = 'baaf363c-9d0b-40de-a76b-948b28182bd2';
```

| id | job_id | model_name | mae | r2 | n_samples | train_window |
|----|--------|------------|-----|----|-----------|--------------|
| 425... | baaf... | daily_tplus1 | 12.97 | 0.636 | 243 | 2024-12-19 ～ 2025-12-18 |

✅ **検証OK**: メトリクスがDBに正常保存され、job_idでリンクされている

#### 5.3.3 JOINクエリ

```sql
SELECT
    fj.id AS job_id,
    fj.target_date,
    fj.status,
    dfr.median,
    mm.mae,
    mm.r2
FROM forecast.forecast_jobs fj
LEFT JOIN forecast.daily_forecast_results dfr ON fj.id = dfr.job_id
LEFT JOIN forecast.model_metrics mm ON fj.id = mm.job_id
WHERE fj.id = 'baaf363c-9d0b-40de-a76b-948b28182bd2';
```

| job_id | target_date | status | median | mae | r2 |
|--------|-------------|--------|--------|-----|----|
| baaf... | 2025-12-19 | succeeded | 85.687 | 12.97 | 0.636 |

✅ **検証OK**: 3テーブルのリレーションが正常に機能している

#### 5.3.4 ログ確認

```json
{
  "timestamp": "2025-12-18T18:10:39",
  "level": "INFO",
  "logger": "app.application.run_daily_tplus1_forecast_with_training",
  "message": "✅ Saved model metrics to DB",
  "metrics_id": "425b0f04-b7c6-4f07-ab34-d7ac4509b3d1",
  "job_id": "baaf363c-9d0b-40de-a76b-948b28182bd2",
  "mae": 12.966932246346783,
  "r2": 0.6357201616067465,
  "n_samples": 243
}
```

✅ **検証OK**: ログにメトリクス保存成功が記録されている

---

## 6. メトリクス品質評価

### 6.1 最新メトリクス（2025-12-19予測）

| 指標 | 値 | 目標値 | 判定 |
|-----|-----|-------|-----|
| MAE (平均絶対誤差) | 12.97 ton | ≤ 12.0 ton | 🟡 許容範囲内（目標にほぼ到達） |
| R2 (決定係数) | 0.636 | ≥ 0.70 | ⚠️ 改善余地あり |
| n_samples (評価日数) | 243 days | ≥ 200 days | ✅ 十分 |
| mae_sum_only (総和MAE) | 34.71 ton | - | - |
| r2_sum_only (総和R2) | -0.596 | - | ❌ 総和予測は精度低い |

### 6.2 前回（2025-12-17）との比較

| 指標 | 2025-12-17 | 2025-12-19 | 変化 |
|-----|-----------|-----------|------|
| MAE | 13.56 ton | 12.97 ton | ✅ **4.3% 改善** |
| R2 | 0.605 | 0.636 | ✅ **5.1% 改善** |
| n_samples | 245 days | 243 days | - |

### 6.3 推奨アクション

1. **短期（1週間）**:
   - ✅ メトリクスDB保存機能の継続監視
   - 🔄 R2 < 0.6のケースでアラート設定

2. **中期（1ヶ月）**:
   - 特徴量エンジニアリング（曜日、月、祝日、予約数等）
   - ハイパーパラメータチューニング
   - バックテスト自動化（予測-実績突合）

3. **長期（3ヶ月）**:
   - アンサンブルモデル検討（LightGBM + Quantile回帰）
   - メトリクスダッシュボード構築（Grafana/Superset）

---

## 7. 技術的工夫

### 7.1 方針選択の理由

**方針A（採用）**: 既存の`scores_walkforward.json`を読み取る

**方針B（不採用）**: `train_daily_model.py`を変更してDB直接保存

**採用理由**:
- ✅ 最小変更原則（train_daily_model.pyは変更不要）
- ✅ 責任分離（学習スクリプトはスクリプトの責務のみ）
- ✅ Clean Architecture準拠（UseCaseがビジネスロジック管理）
- ✅ ロールバック容易（DBマイグレーションのみ）

### 7.2 エラーハンドリング

```python
# UseCase内でのエラーハンドリング
try:
    metrics_id = self._model_metrics_repo.save_metrics(metrics)
    logger.info("✅ Saved model metrics to DB", ...)
except Exception as e:
    logger.error("❌ Failed to save model metrics", exc_info=True, ...)
    # 予測結果保存は成功しているため、ジョブ全体は失敗させない
```

**設計判断**:
- メトリクス保存失敗でもジョブを失敗させない（予測結果保存が主目的）
- エラーログで監視可能（Grafana/Datadogでアラート設定可能）

### 7.3 SQLAlchemy text() vs ORM

**採用**: `text()` ベースのクエリ  
**理由**:
- ✅ 既存コード（DailyForecastResultRepository）との一貫性
- ✅ 複雑なJSONB操作に対応しやすい
- ✅ パフォーマンス（直接SQL）

---

## 8. 今後の拡張性

### 8.1 メトリクス追加

```python
# model_metrics_repository.py に追加可能
class ModelMetrics:
    # ... existing fields ...
    precision_at_threshold: Optional[float] = None  # 閾値精度
    recall_at_threshold: Optional[float] = None     # 閾値再現率
    coverage_80pct: Optional[float] = None          # 80%区間カバレッジ率
```

### 8.2 アラート機能

```python
# UseCase内で閾値チェック
if metrics.r2 < 0.6:
    logger.warning(
        "⚠️ Low R2 score detected",
        extra={"r2": metrics.r2, "threshold": 0.6}
    )
    # Slack/PagerDuty通知（将来実装）
```

### 8.3 メトリクス可視化API

```python
# core_api/routers/forecast.py（将来実装）
@router.get("/metrics/recent")
async def get_recent_metrics(
    model_name: str = "daily_tplus1",
    limit: int = 30
):
    """最近のモデル精度指標を取得"""
    metrics = model_metrics_repo.list_recent(model_name, limit)
    return {
        "metrics": [m.dict() for m in metrics],
        "average_mae": mean([m.mae for m in metrics]),
        "average_r2": mean([m.r2 for m in metrics])
    }
```

---

## 9. 結論

### 9.1 達成内容

- ✅ **データ契約確立**: forecast.model_metricsテーブルで精度指標を永続化
- ✅ **トレーサビリティ**: job_idでforecast_jobs ↔ model_metrics ↔ daily_forecast_resultsをリンク
- ✅ **Clean Architecture**: Port/Adapter パターンで保守性・拡張性確保
- ✅ **E2E検証**: 新規予測実行 → DB検証 → メトリクス確認完了
- ✅ **監査証跡**: メトリクスログとDBレコードで監査可能

### 9.2 残課題

- 🔄 **自動アラート**: R2 < 0.6またはMAE > 15 tonで通知機能追加
- 🔄 **バックテスト**: 予測-実績突合の自動化
- 🔄 **ダッシュボード**: Grafana/Supersetでメトリクス可視化

### 9.3 リスク評価

- **低リスク**: データ整合性、スキーマ設計、トレーサビリティ
- **中リスク**: 予測精度の継続監視が必要（R2 < 0.7）

### 9.4 次のステップ

1. メトリクス推移の週次レビュー（毎週月曜）
2. R2 < 0.6のケースでアラート設定（Slack通知）
3. 特徴量追加による精度改善（2026年Q1）

---

**実装完了日**: 2025-12-18  
**レビュー**: 未実施  
**承認**: 未実施  
**次回更新**: メトリクスダッシュボード実装時
