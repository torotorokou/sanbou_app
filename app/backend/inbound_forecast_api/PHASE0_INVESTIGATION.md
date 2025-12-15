# Phase 0: 調査結果メモ

## 既存構造の確認

### 1. DIハブ: `config/di_providers.py`

**場所**: 各サービス（core_api, ledger_api, inbound_forecast_api等）に存在

**パターン**:
```python
# inbound_forecast_api/app/config/di_providers.py
def get_prediction_executor() -> Union[...]:
    """環境変数で実装を切り替え"""
    executor_type = os.getenv("EXECUTOR_TYPE", "service")
    # ... 実装を返す

def get_execute_daily_forecast_usecase() -> ExecuteDailyForecastUseCase:
    prediction_executor = get_prediction_executor()
    return ExecuteDailyForecastUseCase(prediction_executor=prediction_executor)
```

**ルール**:
- 環境変数から設定を取得
- パスはPath型で返す
- UseCaseはDI関数で組み立て

### 2. Router実装パターン

**場所**: `app/api/routers/*.py`

**パターン** (ledger_api/app/api/routers/jobs.py):
```python
from fastapi import APIRouter, HTTPException
from backend_shared.core.domain import JobStatus, JobCreate

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])

@router.post("", response_model=JobStatus)
async def create_job(job_create: JobCreate) -> JobStatus:
    # 1. リクエストを受け取る
    # 2. UseCaseを呼ぶ（DIで注入）
    # 3. レスポンスを返す
    pass
```

**ルール**:
- routerにロジックを書かない
- `new` しない（DIで注入）
- SQLを書かない
- response_modelを明示

### 3. Worker実装パターン

**場所**: 
- `inbound_forecast_api/worker/main.py`
- `plan_worker/`

**パターン** (inbound_forecast_api/worker/main.py):
```python
class ForecastWorker:
    def __init__(self, config):
        # DI: UseCaseを構築
        executor = ScriptBasedPredictionExecutor(scripts_dir=...)
        self.forecast_usecase = ExecuteDailyForecastUseCase(executor)
    
    def run_daily_forecast(self, target_date) -> tuple[bool, str]:
        # UseCaseを実行
        request = DailyForecastRequest(target_date=target_date)
        output = self.forecast_usecase.execute(request)
        return True, "success"
```

**ルール**:
- run-to-completion方式
- UseCaseを使用
- 冪等性保証
- 失敗時は終了コード非0

### 4. Job管理パターン (ledger_api)

**既存実装**: `ledger_api/app/api/routers/jobs.py`

```python
# インメモリストア（本番ではDB）
job_store: Dict[str, JobStatus] = {}

@router.post("", response_model=JobStatus)
async def create_job(job_create: JobCreate) -> JobStatus:
    job_id = str(uuid.uuid4())
    job_status = JobStatus(
        id=job_id,
        status="pending",
        progress=0,
        message="ジョブを作成しました",
        createdAt=now,
        updatedAt=now,
    )
    job_store[job_id] = job_status
    return job_status

@router.get("/{job_id}", response_model=JobStatus)
async def get_job(job_id: str) -> JobStatus:
    return job_store[job_id]
```

### 5. 予測スクリプトの配置

**場所**: `inbound_forecast_api/app/infra/scripts/`

**4つのモデル**:
1. **日次**: `daily_tplus1_predict.py`, `serve_predict_model_v4_2_4.py`
2. **月次**: `gamma_recency_model/`, `run_monthly_gamma_blend.sh`
3. **週次**: `weekly_allocation/`, `run_weekly_allocation.sh`
4. **着地**: `monthly_landing_gamma_poisson/`, `run_monthly_landing_pipeline.sh`

**出力CSV**:
- 日次: `/backend/output/tplus1_pred_*.csv`
- 月次: `/backend/data/output/gamma_recency_model/blended_future_forecast.csv`
- 週次: `/backend/data/output/gamma_recency_model/weekly_allocated_forecast.csv`
- 着地: `/backend/output/prediction_14d.csv`, `/backend/output/prediction_21d.csv`

### 6. フロントエンド構造

**場所**: `app/frontend/src/`

**パターン**: FSD構造（推測）
- `features/` - 機能ごとのディレクトリ
- `shared/infrastructure/http/` - HTTP通信

**確認必要**:
- 既存のViewModel実装
- Repositoryパターンの実装例

---

## 実装方針

### Phase 1: 結果閲覧のみ

**対象サービス**: `inbound_forecast_api`

**理由**:
- 既存の予測スクリプトがここにある
- 既にworker実装がある
- DIパターンが確立している

**アプローチ**:
1. `inbound_forecast_api/app/api/routers/forecast_results.py` を新設
2. Clean Architecture準拠で実装
3. 既存のDIパターンに従う

---

**調査完了**: 2025-12-15
**次のアクション**: Phase 1実装開始
