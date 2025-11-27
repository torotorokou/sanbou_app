"""Unit Tests for KPIUseCase"""
import pytest
from datetime import date

from app.application.usecases.kpi.kpi_uc import KPIUseCase
from tests.unit.application.fakes.fake_kpi_port import FakeKPIQueryPort


class TestKPIUseCase:
    """Test KPIUseCase with Fake Port (no database dependency)"""
    
    def test_get_overview_with_valid_data(self):
        """Test overview with both job counts and latest date"""
        # Arrange
        fake_port = FakeKPIQueryPort(
            forecast_job_counts={"pending": 5, "running": 2, "completed": 100, "failed": 3},
            latest_prediction_date=date(2025, 5, 15),
        )
        uc = KPIUseCase(kpi_query=fake_port)
        
        # Act
        result = uc.get_overview()
        
        # Assert
        assert result.total_jobs == 110  # 5+2+100+3
        assert result.completed_jobs == 100
        assert result.failed_jobs == 3
        assert result.latest_prediction_date == date(2025, 5, 15)
    
    def test_get_overview_with_no_predictions(self):
        """Test overview when no predictions exist (latest_date = None)"""
        # Arrange
        fake_port = FakeKPIQueryPort(
            forecast_job_counts={"pending": 0, "running": 0, "completed": 0, "failed": 0},
            latest_prediction_date=None,
        )
        uc = KPIUseCase(kpi_query=fake_port)
        
        # Act
        result = uc.get_overview()
        
        # Assert
        assert result.total_jobs == 0
        assert result.completed_jobs == 0
        assert result.failed_jobs == 0
        assert result.latest_prediction_date is None
    
    def test_get_overview_with_only_completed_jobs(self):
        """Test overview with only completed jobs"""
        # Arrange
        fake_port = FakeKPIQueryPort(
            forecast_job_counts={"pending": 0, "running": 0, "completed": 50, "failed": 0},
            latest_prediction_date=date(2025, 6, 1),
        )
        uc = KPIUseCase(kpi_query=fake_port)
        
        # Act
        result = uc.get_overview()
        
        # Assert
        assert result.total_jobs == 50
        assert result.completed_jobs == 50
        assert result.failed_jobs == 0
        assert result.latest_prediction_date == date(2025, 6, 1)
    
    def test_get_overview_stateless(self):
        """Test that UseCase is stateless (no side effects between calls)"""
        # Arrange
        fake_port = FakeKPIQueryPort(
            forecast_job_counts={"pending": 1, "running": 1, "completed": 1, "failed": 1},
            latest_prediction_date=date(2025, 7, 1),
        )
        uc = KPIUseCase(kpi_query=fake_port)
        
        # Act
        result1 = uc.get_overview()
        result2 = uc.get_overview()
        
        # Assert - both calls return identical results
        assert result1.total_jobs == result2.total_jobs == 4
        assert result1.completed_jobs == result2.completed_jobs == 1
        assert result1.latest_prediction_date == result2.latest_prediction_date
