"""
Forecast Job V2 Schemas

forecast.forecast_jobs テーブル用のHTTP Request/Response schemas
"""
from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class SubmitDailyTplus1JobRequest(BaseModel):
    """日次t+1予測ジョブ投入リクエスト"""
    target_date: Optional[date] = Field(
        default=None,
        description="予測対象日（省略時は明日JST）"
    )


class ForecastJobV2Response(BaseModel):
    """予測ジョブレスポンス"""
    id: UUID = Field(description="ジョブID")
    job_type: str = Field(description="ジョブタイプ（daily_tplus1等）")
    target_date: date = Field(description="予測対象日")
    status: str = Field(description="ジョブステータス（queued/running/succeeded/failed）")
    run_after: datetime = Field(description="実行可能時刻")
    attempt: int = Field(description="試行回数")
    max_attempt: int = Field(description="最大試行回数")
    input_snapshot: dict = Field(description="入力パラメータのスナップショット")
    last_error: Optional[str] = Field(default=None, description="最後のエラーメッセージ")
    created_at: datetime = Field(description="作成日時")
    updated_at: datetime = Field(description="更新日時")
    started_at: Optional[datetime] = Field(default=None, description="実行開始日時")
    finished_at: Optional[datetime] = Field(default=None, description="実行終了日時")
    
    model_config = ConfigDict(from_attributes=True)
