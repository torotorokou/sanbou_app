# Inbound Forecast - 次のステップ

**作成日**: 2025-12-15  
**優先度**: 高

## 現状の問題点

### 🔴 Problem 1: ジョブ作成エンドポイントの検証バグ

**ファイル**: `app/backend/core_api/app/core/usecases/forecast/forecast_job_uc.py`

**症状**:
```bash
curl -X POST http://localhost:8003/core_api/forecast/jobs \
  -d '{"target_from": "2025-01-20", "target_to": "2025-01-20", ...}'
# → エラー: "予測期間は最低1日必要です（指定: 0日）"
```

**原因**:
- target_from と target_to が同じ日付の場合、期間が0日と計算される
- 日次予測では1日分の予測が必要なので、target_to は翌日を期待

**影響**: フロントエンドからのジョブ作成が不可

**修正方針**:
- Option A: 検証ロジックを修正（同じ日付でも1日分として許可）
- Option B: スキーマを変更（target_date のみ受け取る）

### 🟡 Problem 2: DB保存機能未実装

**ファイル**: `app/backend/inbound_forecast_api/app/infra/prediction/script_executor.py`

**症状**: CSV生成のみで、`forecast.predictions_daily`テーブルに保存されない

**影響**: フロントエンドから予測結果を取得できない

**修正方針**:
1. CSVをpandasで読み込み
2. `forecast.predictions_daily`テーブルにUPSERT
3. 冪等性保証（同じ日付は上書き）

## 次のタスク

### Task 1: ジョブ作成バグの修正 (優先度: 高)

**Goal**: `POST /forecast/jobs` で1日分の予測ジョブを作成可能にする

**Steps**:
1. `CreateForecastJobUseCase.execute()` の検証ロジックを確認
2. 日付範囲の計算ロジックを修正
3. ユニットテスト追加
4. 動作確認

**Expected Result**:
```bash
curl -X POST http://localhost:8003/core_api/forecast/jobs \
  -d '{"target_from": "2025-01-20", "target_to": "2025-01-21", ...}'
# → {"id": 123, "status": "queued", ...}
```

### Task 2: DB保存機能の実装 (優先度: 高)

**Goal**: 予測結果をDBに保存し、APIから取得可能にする

**Steps**:
1. `ScriptBasedPredictionExecutor` にDB保存ロジック追加
2. CSV → pandas DataFrame → SQLAlchemy ORM
3. `forecast.predictions_daily` への UPSERT
4. エラーハンドリング（CSV読み込み失敗、DB接続失敗）
5. 動作確認

**Expected Result**:
```bash
make forecast-run TARGET_DATE=2025-01-20
# → CSV生成 + DB保存完了

curl http://localhost:8003/core_api/forecast/predictions?from=2025-01-20&to=2025-01-21
# → [{"prediction_date": "2025-01-20", "yard_code": "Y001", ...}, ...]
```

### Task 3: エンドツーエンドテスト (優先度: 中)

**Goal**: UI → API → Worker → DB の完全フロー確認

**Steps**:
1. フロントエンドに「予測実行ボタン」追加
2. ボタンクリック → ジョブ作成API呼び出し
3. ジョブIDを取得 → executeエンドポイント呼び出し
4. ポーリングでステータス確認
5. 完了後、予測結果を表示

## 技術的詳細

### スキーマ変更案（Option B）

```python
# 現在
class ForecastJobCreate(BaseModel):
    target_from: date_type
    target_to: date_type
    job_type: str = "daily"

# 変更案
class ForecastJobCreate(BaseModel):
    target_date: date_type  # 予測対象日
    job_type: str = "daily"
    
    # target_from/target_toは自動計算
    @property
    def target_from(self) -> date_type:
        return self.target_date
    
    @property
    def target_to(self) -> date_type:
        return self.target_date + timedelta(days=1)
```

### DB保存実装例

```python
class ScriptBasedPredictionExecutor:
    def __init__(self, scripts_dir: Path, db_session: Session):
        self.scripts_dir = scripts_dir
        self.db_session = db_session
        
    def execute_daily_forecast(self, target_date: Optional[date] = None) -> str:
        # 1. 予測実行（既存ロジック）
        csv_path = self._run_prediction_script(target_date)
        
        # 2. CSV読み込み
        df = pd.read_csv(csv_path)
        
        # 3. DB保存
        self._save_to_db(df, target_date)
        
        return csv_path
    
    def _save_to_db(self, df: pd.DataFrame, target_date: date):
        """予測結果をDBに保存（UPSERT）"""
        for _, row in df.iterrows():
            stmt = (
                insert(PredictionDaily)
                .values(
                    prediction_date=target_date,
                    yard_code=row['yard_code'],
                    predicted_volume=row['predicted_volume'],
                    # ...
                )
                .on_conflict_do_update(
                    index_elements=['prediction_date', 'yard_code'],
                    set_=dict(
                        predicted_volume=row['predicted_volume'],
                        updated_at=datetime.utcnow(),
                    )
                )
            )
            self.db_session.execute(stmt)
        
        self.db_session.commit()
```

## 見積もり

- Task 1: 1-2時間
- Task 2: 2-3時間
- Task 3: 3-4時間

**合計**: 6-9時間

## 次のアクション

1. Task 1のジョブ作成バグを修正
2. Task 2のDB保存機能を実装
3. Task 3のE2Eテストを実施

---

**最終更新**: 2025-12-15
