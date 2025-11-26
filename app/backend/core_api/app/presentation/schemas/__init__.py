"""
Presentation Layer Schemas (Pydantic DTOs)

HTTP Request/Response schemas for FastAPI routers.
These are framework-specific (Pydantic) and should NOT be imported by domain or application layers.
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

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


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
# Customer Churn DTOs
# ========================================

class CustomerChurnAnalyzeRequest(BaseModel):
    """Request to analyze customer churn."""
    current_start: date_type = Field(description="Current period start date (YYYY-MM-DD)")
    current_end: date_type = Field(description="Current period end date (YYYY-MM-DD)")
    previous_start: date_type = Field(description="Previous period start date (YYYY-MM-DD)")
    previous_end: date_type = Field(description="Previous period end date (YYYY-MM-DD)")


class LostCustomerDTO(BaseModel):
    """Lost customer data transfer object."""
    customer_id: str = Field(description="Customer ID")
    customer_name: str = Field(description="Customer name")
    sales_rep_id: Optional[str] = Field(default=None, description="Sales representative ID")
    sales_rep_name: Optional[str] = Field(default=None, description="Sales representative name")
    last_visit_date: date_type = Field(description="Last visit date in previous period")
    prev_visit_days: int = Field(description="Number of visit days in previous period")
    prev_total_amount_yen: float = Field(description="Total amount in yen for previous period")
    prev_total_qty_kg: float = Field(description="Total quantity in kg for previous period")

    model_config = ConfigDict(from_attributes=True)


class CustomerChurnAnalyzeResponse(BaseModel):
    """Response for customer churn analysis."""
    lost_customers: list[LostCustomerDTO] = Field(description="List of lost customers")


# ========================================
# Sales Rep DTOs
# ========================================

class SalesRepDTO(BaseModel):
    """Sales representative data."""
    sales_rep_id: str = Field(description="Sales rep ID")
    sales_rep_name: str = Field(description="Sales rep name")

    model_config = ConfigDict(from_attributes=True)


class SalesRepListResponse(BaseModel):
    """Response for sales rep list."""
    sales_reps: list[SalesRepDTO] = Field(description="List of sales representatives")


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
    # New fields for achievement mode calculation (cumulative to yesterday vs. total at period end)
    month_target_to_date_ton: Optional[float] = Field(default=None, description="Monthly cumulative target (month_start to yesterday)")
    month_target_total_ton: Optional[float] = Field(default=None, description="Monthly total target (entire month)")
    week_target_to_date_ton: Optional[float] = Field(default=None, description="Weekly cumulative target (week_start to yesterday)")
    week_target_total_ton: Optional[float] = Field(default=None, description="Weekly total target (entire week)")
    month_actual_to_date_ton: Optional[float] = Field(default=None, description="Monthly cumulative actual (month_start to yesterday)")
    week_actual_to_date_ton: Optional[float] = Field(default=None, description="Weekly cumulative actual (week_start to yesterday)")

