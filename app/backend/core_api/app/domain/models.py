"""
Domain models and DTOs (Pydantic v2).
Framework-agnostic: no FastAPI dependencies.

設計方針:
  - 現在は主にDTO（Data Transfer Object）を定義
  - 将来的にエンティティは domain/entities/ へ移動予定
  - 将来的に値オブジェクトは domain/value_objects/ へ移動予定
  - ビジネスロジックは外部依存ゼロで記述
"""
from datetime import date as date_type, datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# ========================================
# Job DTOs
# ========================================

class ForecastJobCreate(BaseModel):
    """Request to create a forecast job."""
    job_type: str = Field(default="daily", description="Type of forecast job")
    target_from: date_type = Field(description="Start date of forecast range")
    target_to: date_type = Field(description="End date of forecast range")
    actor: Optional[str] = Field(default="system", description="User or system actor")
    payload_json: Optional[dict] = Field(default=None, description="Additional job parameters")


class ForecastJobResponse(BaseModel):
    """Response after creating or querying a forecast job."""
    id: int
    job_type: str
    target_from: date_type
    target_to: date_type
    status: str  # queued | running | done | failed
    attempts: int
    scheduled_for: Optional[datetime]
    actor: Optional[str]
    payload_json: Optional[dict]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========================================
# Prediction DTOs
# ========================================

class PredictionDTO(BaseModel):
    """Daily prediction result."""
    date: date_type
    y_hat: float = Field(description="Predicted value")
    y_lo: Optional[float] = Field(default=None, description="Lower bound")
    y_hi: Optional[float] = Field(default=None, description="Upper bound")
    model_version: Optional[str] = Field(default=None, description="Model version used")
    generated_at: Optional[datetime] = Field(default=None, description="When prediction was generated")

    model_config = ConfigDict(from_attributes=True)


# ========================================
# Ingest DTOs
# ========================================

class ReservationCreate(BaseModel):
    """Request to create an inbound reservation."""
    date: date_type = Field(description="Reservation date (YYYY-MM-DD)")
    trucks: int = Field(ge=0, description="Number of trucks reserved")


class ReservationResponse(BaseModel):
    """Response after creating a reservation."""
    date: date_type
    trucks: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========================================
# KPI DTOs
# ========================================

class KPIOverview(BaseModel):
    """
    Overview KPI DTO for frontend dashboard.
    TODO: Replace with real aggregation queries.
    """
    total_jobs: int = Field(default=0, description="Total number of forecast jobs")
    completed_jobs: int = Field(default=0, description="Completed jobs")
    failed_jobs: int = Field(default=0, description="Failed jobs")
    latest_prediction_date: Optional[date_type] = Field(default=None, description="Latest prediction date available")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")


# ========================================
# External API DTOs
# ========================================

class RAGAskRequest(BaseModel):
    """Request to RAG API /ask endpoint."""
    query: str = Field(description="User query for RAG")


class RAGAskResponse(BaseModel):
    """Response from RAG API."""
    answer: str
    sources: Optional[list[str]] = None


class ManualListResponse(BaseModel):
    """Response from Manual API /list endpoint."""
    manuals: list[dict]  # TODO: define proper schema when manual_api contract is clarified


# ========================================
# Dashboard Target DTOs
# ========================================

class TargetMetricsResponse(BaseModel):
    """Response for dashboard target metrics with actuals."""
    ddate: Optional[date_type] = Field(default=None, description="Data date")
    month_target_ton: Optional[float] = Field(default=None, description="Monthly target in tons")
    week_target_ton: Optional[float] = Field(default=None, description="Weekly target in tons")
    day_target_ton: Optional[float] = Field(default=None, description="Daily target in tons")
    month_actual_ton: Optional[float] = Field(default=None, description="Monthly actual in tons")
    week_actual_ton: Optional[float] = Field(default=None, description="Weekly actual in tons")
    day_actual_ton_prev: Optional[float] = Field(default=None, description="Previous day actual in tons")
    iso_year: Optional[int] = Field(default=None, description="ISO year")
    iso_week: Optional[int] = Field(default=None, description="ISO week number")
    iso_dow: Optional[int] = Field(default=None, description="ISO day of week (1=Monday, 7=Sunday)")
    day_type: Optional[str] = Field(default=None, description="Day type (weekday/sat/sun_hol)")
    is_business: Optional[bool] = Field(default=None, description="Is business day")

