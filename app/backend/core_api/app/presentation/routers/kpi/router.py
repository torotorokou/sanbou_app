"""
KPI API Router
KPI overview and metrics endpoints

Design:
  - Thin router layer (3-step pattern)
  - Request → Input DTO → UseCase → Output DTO → Response
  - No business logic in this layer
"""
from fastapi import APIRouter, Depends

from app.presentation.schemas import KPIOverview
from app.application.usecases.kpi.kpi_uc import KPIUseCase
from app.application.usecases.kpi.dto import GetKPIOverviewInput
from app.config.di_providers import get_kpi_uc

router = APIRouter(prefix="/kpi", tags=["kpi"])


@router.get("/overview", response_model=KPIOverview, summary="Get KPI overview")
def get_overview(
    uc: KPIUseCase = Depends(get_kpi_uc),
):
    """
    Get aggregated KPIs for the dashboard.
    Follows Clean Architecture with 3-step pattern:
      1. Request → Input DTO (empty input)
      2. UseCase execution
      3. Output DTO → Response
    """
    # Step 1: Request → Input DTO (no parameters needed)
    input_dto = GetKPIOverviewInput()
    
    # Step 2: UseCase execution
    output_dto = uc.execute(input_dto)
    
    # Step 3: Output DTO → Response
    return KPIOverview(
        total_jobs=output_dto.total_jobs,
        completed_jobs=output_dto.completed_jobs,
        failed_jobs=output_dto.failed_jobs,
        latest_prediction_date=output_dto.latest_prediction_date,
    )
