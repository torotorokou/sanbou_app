"""
KPI UseCase: aggregations and queries for dashboard.

Port-based implementation following Clean Architecture principles.

Design:
  - execute() method with Input/Output DTO pattern
  - Port abstraction for data access (no direct DB access)
  - Business logic concentrated in UseCase layer
"""
from app.domain.ports.kpi_port import KPIQueryPort
from app.application.usecases.kpi.dto import GetKPIOverviewInput, GetKPIOverviewOutput


class KPIUseCase:
    """
    UseCase for KPI overview retrieval
    
    Responsibilities:
      - Aggregate KPI metrics from multiple sources via Port
      - Apply business rules (e.g., calculation logic)
      - Return structured output via DTO
    """

    def __init__(self, kpi_query: KPIQueryPort):
        """
        Args:
            kpi_query: KPI query port implementation
        """
        self.kpi_query = kpi_query

    def execute(self, input_dto: GetKPIOverviewInput) -> GetKPIOverviewOutput:
        """
        Get aggregated KPI overview
        
        Process:
          1. Fetch job counts via Port
          2. Fetch latest prediction date via Port
          3. Calculate aggregates
          4. Return structured Output DTO
        
        Args:
            input_dto: Empty input (for consistency, may add filters later)
            
        Returns:
            GetKPIOverviewOutput: KPI metrics with job counts and dates
        """
        counts = self.kpi_query.get_forecast_job_counts()
        latest_date = self.kpi_query.get_latest_prediction_date()
        
        return GetKPIOverviewOutput(
            total_jobs=sum(counts.values()),
            completed_jobs=counts.get("completed", 0),
            failed_jobs=counts.get("failed", 0),
            latest_prediction_date=latest_date,
        )
