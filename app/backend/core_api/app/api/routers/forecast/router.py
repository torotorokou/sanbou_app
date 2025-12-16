"""
Forecast Router - 予測機能エンドポイント

予測ジョブの作成、ステータス確認、結果取得を提供。

機能:
  - POST /forecast/jobs: 予測ジョブをキューに登録(非同期実行)
  - GET /forecast/jobs/{job_id}: ジョブのステータスを確認
  - GET /forecast/predictions: 予測結果を取得

処理フロー:
  1. フロントエンドがジョブ作成リクエストを送信
  2. Core APIがジョブをDBに登録(status='queued')
  3. forecast_workerがジョブをクレームして実行
  4. 実行後、statusを'done'または'failed'に更新
  5. フロントエンドがステータスをポーリングまたは結果を取得

注意:
  - ジョブ作成は同期処理だが、実行は非同期(バックグラウンド)
  - 長時間実行ジョブのため、ポーリングまたはWebhookで結果を取得

設計方針:
  - カスタム例外を使用(HTTPExceptionは使用しない)
  - NotFoundError でリソース不存在エラーを表現
"""
from fastapi import APIRouter, Depends, Query
from datetime import date as date_type
from sqlalchemy.orm import Session
from uuid import UUID

from app.config.di_providers import (
    get_create_forecast_job_uc,
    get_forecast_job_status_uc,
    get_predictions_uc,
)
from app.core.usecases.forecast.forecast_job_uc import (
    CreateForecastJobUseCase,
    GetForecastJobStatusUseCase,
    GetPredictionsUseCase,
)
from app.api.schemas import ForecastJobCreate, ForecastJobResponse, PredictionDTO
from app.api.schemas.forecast_job_v2_schema import (
    SubmitDailyTplus1JobRequest,
    ForecastJobV2Response
)
from app.core.usecases.forecast.submit_daily_tplus1_job_uc import (
    SubmitDailyTplus1JobUseCase
)
from app.core.ports.forecast_job_repository_port_v2 import DuplicateJobError
from app.deps import get_db
from backend_shared.core.domain.exceptions import NotFoundError

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.post("/jobs", response_model=ForecastJobResponse, summary="Create forecast job")
def create_forecast_job(
    req: ForecastJobCreate,
    uc: CreateForecastJobUseCase = Depends(get_create_forecast_job_uc),
):
    """
    Queue a new forecast job.
    The job will be picked up by forecast_worker and executed asynchronously.
    """
    return uc.execute(req)


@router.get("/jobs/{job_id}", response_model=ForecastJobResponse, summary="Get job status")
def get_job_status(
    job_id: int,
    uc: GetForecastJobStatusUseCase = Depends(get_forecast_job_status_uc),
):
    """
    Retrieve the status and metadata of a forecast job.
    """
    job = uc.execute(job_id)
    if not job:
        raise NotFoundError(entity="ForecastJob", entity_id=job_id)
    return job


@router.get("/predictions", response_model=list[PredictionDTO], summary="Get predictions")
def get_predictions(
    from_date: date_type = Query(..., alias="from", description="Start date (YYYY-MM-DD)"),
    to_date: date_type = Query(..., alias="to", description="End date (YYYY-MM-DD)"),
    uc: GetPredictionsUseCase = Depends(get_predictions_uc),
):
    """
    Retrieve forecast predictions within the specified date range.
    """
    return uc.execute(from_=from_date, to_=to_date)


# ========================================
# V2 Endpoints (forecast.forecast_jobs)
# ========================================

@router.post(
    "/jobs/daily-tplus1",
    response_model=ForecastJobV2Response,
    summary="Submit daily t+1 forecast job",
    description="日次t+1予測ジョブを手動投入します。既に queued/running のジョブがあれば既存ジョブを返します。"
)
def submit_daily_tplus1_job(
    req: SubmitDailyTplus1JobRequest,
    db: Session = Depends(get_db)
):
    """
    日次t+1予測ジョブを投入
    
    - 既に queued/running のジョブがあれば既存ジョブを返す（重複投入を防止）
    - target_date 省略時は明日（JST）を予測対象とする
    """
    from app.infra.adapters.forecast.forecast_job_repository_v2 import (
        PostgresForecastJobRepositoryV2
    )
    
    repo = PostgresForecastJobRepositoryV2(db)
    uc = SubmitDailyTplus1JobUseCase(repo)
    
    job = uc.execute(requested_date=req.target_date)
    
    return ForecastJobV2Response.model_validate(job)


@router.get(
    "/jobs/v2/{job_id}",
    response_model=ForecastJobV2Response,
    summary="Get forecast job by ID (V2)",
    description="ジョブIDで予測ジョブを取得します（forecast.forecast_jobs テーブル用）。"
)
def get_forecast_job_v2(
    job_id: UUID,
    db: Session = Depends(get_db)
):
    """
    ジョブIDで予測ジョブを取得
    """
    from app.infra.adapters.forecast.forecast_job_repository_v2 import (
        PostgresForecastJobRepositoryV2
    )
    
    repo = PostgresForecastJobRepositoryV2(db)
    job = repo.get_job_by_id(job_id)
    
    if job is None:
        raise NotFoundError(entity="ForecastJob", entity_id=str(job_id))
    
    return ForecastJobV2Response.model_validate(job)
