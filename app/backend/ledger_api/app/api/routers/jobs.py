"""
ジョブ管理API（サンプル実装）

目的:
- 非同期処理のジョブ状態を管理
- 失敗時に ProblemDetails を返す

使用例:
    POST /api/jobs - ジョブを作成
    GET /api/jobs/{job_id} - ジョブの状態を取得
"""

import uuid
from datetime import datetime
from typing import Dict

from backend_shared.core.domain import JobCreate, JobStatus, ProblemDetails
from backend_shared.infra.adapters.fastapi import DomainError
from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])

# 簡易的なインメモリストア（本番ではRedis/DBを使用）
job_store: Dict[str, JobStatus] = {}


@router.post("", response_model=JobStatus)
async def create_job(request: Request, job_create: JobCreate) -> JobStatus:
    """
    ジョブを作成

    リクエスト:
        - feature: 機能名
        - parameters: パラメータ（任意）

    レスポンス:
        - JobStatus
    """
    job_id = str(uuid.uuid4())

    now = datetime.utcnow().isoformat()

    job_status = JobStatus(
        id=job_id,
        status="pending",
        progress=0,
        message="ジョブを作成しました",
        createdAt=now,
        updatedAt=now,
    )

    job_store[job_id] = job_status

    # 非同期処理を開始（本番では Celery/BackgroundTasks 等を使用）
    # ここではサンプルとしてストアに保存するだけ

    return job_status


@router.get("/{job_id}", response_model=JobStatus)
async def get_job(job_id: str) -> JobStatus:
    """
    ジョブの状態を取得

    レスポンス:
        - JobStatus（失敗時は error に ProblemDetails が含まれる）
    """
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="ジョブが見つかりません")

    return job_store[job_id]


@router.post("/{job_id}/fail", response_model=JobStatus)
async def fail_job(request: Request, job_id: str) -> JobStatus:
    """
    【テスト用】ジョブを失敗させる

    ProblemDetails を含むエラー状態にする
    """
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="ジョブが見つかりません")

    trace_id = getattr(request.state, "trace_id", None)

    # ProblemDetails を作成
    error = ProblemDetails(
        status=500,
        code="PROCESSING_ERROR",
        userMessage="処理中にエラーが発生しました",
        title="処理エラー",
        traceId=trace_id,
    )

    # ジョブを失敗状態に更新
    job = job_store[job_id]
    job.status = "failed"
    job.progress = 0
    job.message = "処理に失敗しました"
    job.error = error
    job.updatedAt = datetime.utcnow().isoformat()

    return job


@router.post("/{job_id}/raise-error")
async def raise_error(job_id: str):
    """
    【テスト用】DomainError を発生させる

    エラーハンドラによって ProblemDetails に変換される
    """
    raise DomainError(
        code="TEST_ERROR",
        status=422,
        user_message="これはテストエラーです",
        title="テストエラー",
    )
