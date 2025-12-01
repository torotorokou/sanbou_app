"""Unit Tests for Calendar UseCase"""
import pytest
from datetime import date

from app.core.usecases.calendar.get_calendar_month_uc import GetCalendarMonthUseCase

from tests.unit.application.fakes.fake_ports import FakeCalendarQuery


class TestGetCalendarMonthUseCase:
    """Test GetCalendarMonthUseCase with Fake Port (no database dependency)"""
    
    def test_get_month_calendar_with_valid_data(self):
        """Test calendar retrieval with valid year and month"""
        # Arrange
        test_data = [
            {
                "ddate": date(2025, 1, 1),
                "y": 2025,
                "m": 1,
                "iso_year": 2025,
                "iso_week": 1,
                "iso_dow": 3,
                "is_holiday": True,
                "is_second_sunday": False,
                "is_company_closed": True,
                "day_type": "holiday",
                "is_business": False,
            },
            {
                "ddate": date(2025, 1, 2),
                "y": 2025,
                "m": 1,
                "iso_year": 2025,
                "iso_week": 1,
                "iso_dow": 4,
                "is_holiday": False,
                "is_second_sunday": False,
                "is_company_closed": False,
                "day_type": "weekday",
                "is_business": True,
            },
        ]
        fake_port = FakeCalendarQuery(calendar_data=test_data)
        uc = GetCalendarMonthUseCase(query=fake_port)
        
        # Act
        result = uc.execute(year=2025, month=1)
        
        # Assert
        assert len(result) == 2
        assert result[0]["ddate"] == date(2025, 1, 1)
        assert result[0]["is_business"] is False
        assert result[1]["ddate"] == date(2025, 1, 2)
        assert result[1]["is_business"] is True
    
    def test_get_month_calendar_with_empty_data(self):
        """Test calendar retrieval when no data exists"""
        # Arrange
        fake_port = FakeCalendarQuery(calendar_data=[])
        uc = GetCalendarMonthUseCase(query=fake_port)
        
        # Act
        result = uc.execute(year=2025, month=12)
        
        # Assert
        assert result == []
    
    def test_invalid_year_too_low(self):
        """Test validation error when year is below 1900"""
        # Arrange
        fake_port = FakeCalendarQuery()
        uc = GetCalendarMonthUseCase(query=fake_port)
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            uc.execute(year=1899, month=1)
        
        assert "must be 1900-2100" in str(exc_info.value)
    
    def test_invalid_year_too_high(self):
        """Test validation error when year is above 2100"""
        # Arrange
        fake_port = FakeCalendarQuery()
        uc = GetCalendarMonthUseCase(query=fake_port)
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            uc.execute(year=2101, month=1)
        
        assert "must be 1900-2100" in str(exc_info.value)
    
    def test_invalid_month_too_low(self):
        """Test validation error when month is below 1"""
        # Arrange
        fake_port = FakeCalendarQuery()
        uc = GetCalendarMonthUseCase(query=fake_port)
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            uc.execute(year=2025, month=0)
        
        assert "must be 1-12" in str(exc_info.value)
    
    def test_invalid_month_too_high(self):
        """Test validation error when month is above 12"""
        # Arrange
        fake_port = FakeCalendarQuery()
        uc = GetCalendarMonthUseCase(query=fake_port)
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            uc.execute(year=2025, month=13)
        
        assert "must be 1-12" in str(exc_info.value)
    
    def test_boundary_year_1900(self):
        """Test boundary value: year = 1900 (valid)"""
        # Arrange
        fake_port = FakeCalendarQuery(calendar_data=[])
        uc = GetCalendarMonthUseCase(query=fake_port)
        
        # Act
        result = uc.execute(year=1900, month=1)
        
        # Assert
        assert result == []  # No error raised
    
    def test_boundary_year_2100(self):
        """Test boundary value: year = 2100 (valid)"""
        # Arrange
        fake_port = FakeCalendarQuery(calendar_data=[])
        uc = GetCalendarMonthUseCase(query=fake_port)
        
        # Act
        result = uc.execute(year=2100, month=12)
        
        # Assert
        assert result == []  # No error raised
    
    def test_boundary_month_1(self):
        """Test boundary value: month = 1 (valid)"""
        # Arrange
        fake_port = FakeCalendarQuery(calendar_data=[])
        uc = GetCalendarMonthUseCase(query=fake_port)
        
        # Act
        result = uc.execute(year=2025, month=1)
        
        # Assert
        assert result == []  # No error raised
    
    def test_boundary_month_12(self):
        """Test boundary value: month = 12 (valid)"""
        # Arrange
        fake_port = FakeCalendarQuery(calendar_data=[])
        uc = GetCalendarMonthUseCase(query=fake_port)
        
        # Act
        result = uc.execute(year=2025, month=12)
        
        # Assert
        assert result == []  # No error raised
