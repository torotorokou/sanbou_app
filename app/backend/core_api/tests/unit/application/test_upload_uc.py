"""Unit Tests for Upload UseCases"""

from datetime import date, datetime
from unittest.mock import Mock

import pytest

from app.core.usecases.upload.delete_upload_scope_uc import DeleteUploadScopeUseCase
from app.core.usecases.upload.get_upload_calendar_uc import GetUploadCalendarUseCase
from app.core.usecases.upload.get_upload_status_uc import GetUploadStatusUseCase
from tests.unit.application.fakes.fake_ports import FakeUploadStatusQuery


class TestGetUploadStatusUseCase:
    """Test GetUploadStatusUseCase with Fake Port"""

    def test_get_status_with_existing_file(self):
        """Test retrieving status for existing upload file"""
        # Arrange
        test_status = {
            "upload_file_id": 123,
            "csv_kind": "receive",
            "target_date": date(2025, 11, 1),
            "filename": "test_receive.csv",
            "uploaded_at": datetime(2025, 11, 1, 10, 30, 0),
            "row_count": 100,
            "status": "completed",
        }
        fake_port = FakeUploadStatusQuery(upload_status=test_status)
        uc = GetUploadStatusUseCase(query=fake_port)

        # Act
        result = uc.execute(upload_file_id=123)

        # Assert
        assert result is not None
        assert result["upload_file_id"] == 123

        assert result["status"] == "completed"
        assert result["row_count"] == 100

    def test_get_status_with_nonexistent_file(self):
        """Test retrieving status for non-existent upload file"""
        # Arrange
        fake_port = FakeUploadStatusQuery(upload_status=None)
        uc = GetUploadStatusUseCase(query=fake_port)

        # Act
        result = uc.execute(upload_file_id=999)

        # Assert
        assert result is None

    def test_invalid_upload_file_id_negative(self):
        """Test validation error when upload_file_id is negative"""
        # Arrange
        fake_port = FakeUploadStatusQuery()
        uc = GetUploadStatusUseCase(query=fake_port)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            uc.execute(upload_file_id=-1)

        assert "Invalid upload_file_id" in str(exc_info.value)

    def test_invalid_upload_file_id_zero(self):
        """Test validation error when upload_file_id is zero"""
        # Arrange
        fake_port = FakeUploadStatusQuery()
        uc = GetUploadStatusUseCase(query=fake_port)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            uc.execute(upload_file_id=0)

        assert "Invalid upload_file_id" in str(exc_info.value)


class TestGetUploadCalendarUseCase:
    """Test GetUploadCalendarUseCase with Fake Port"""

    def test_get_calendar_with_data(self):
        """Test retrieving upload calendar with data"""
        # Arrange
        test_calendar = [
            {
                "target_date": date(2025, 11, 1),
                "csv_kind": "receive",
                "upload_count": 3,
                "latest_upload": datetime(2025, 11, 1, 15, 30, 0),
            },
            {
                "target_date": date(2025, 11, 2),
                "csv_kind": "shipment",
                "upload_count": 1,
                "latest_upload": datetime(2025, 11, 2, 9, 0, 0),
            },
        ]
        fake_port = FakeUploadStatusQuery(upload_calendar=test_calendar)
        uc = GetUploadCalendarUseCase(query=fake_port)

        # Act
        result = uc.execute(year=2025, month=11)

        # Assert
        assert len(result) == 2
        assert result[0]["target_date"] == date(2025, 11, 1)
        assert result[0]["upload_count"] == 3
        assert result[1]["target_date"] == date(2025, 11, 2)
        assert result[1]["upload_count"] == 1

    def test_get_calendar_with_empty_data(self):
        """Test retrieving upload calendar when no data exists"""
        # Arrange
        fake_port = FakeUploadStatusQuery(upload_calendar=[])
        uc = GetUploadCalendarUseCase(query=fake_port)

        # Act
        result = uc.execute(year=2025, month=11)

        # Assert
        assert result == []


class TestDeleteUploadScopeUseCase:
    """Test DeleteUploadScopeUseCase with Fake Port"""

    def test_delete_with_valid_data(self):
        """Test deleting upload scope with valid date and kind"""
        # Arrange
        fake_port = FakeUploadStatusQuery()
        mock_db = Mock()
        uc = DeleteUploadScopeUseCase(query=fake_port, db=mock_db)

        # Act
        result = uc.execute(upload_file_id=1, target_date=date(2025, 11, 1), csv_kind="receive")

        # Assert
        assert result == 1

        assert fake_port.get_deleted_count() == 1

    def test_delete_with_empty_csv_kind(self):
        """Test validation error with empty csv_kind"""
        # Arrange
        fake_port = FakeUploadStatusQuery()
        mock_db = Mock()
        uc = DeleteUploadScopeUseCase(query=fake_port, db=mock_db)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            uc.execute(upload_file_id=1, target_date=date(2025, 11, 1), csv_kind="")

        assert "csv_kind" in str(exc_info.value)

    def test_delete_with_receive_kind(self):
        """Test delete with 'receive' kind"""
        # Arrange
        fake_port = FakeUploadStatusQuery()
        mock_db = Mock()
        uc = DeleteUploadScopeUseCase(query=fake_port, db=mock_db)

        # Act
        uc.execute(upload_file_id=1, target_date=date(2025, 11, 15), csv_kind="receive")

        # Assert

        assert fake_port.get_deleted_count() == 1

    def test_delete_with_yard_kind(self):
        """Test delete with 'yard' kind"""
        # Arrange
        fake_port = FakeUploadStatusQuery()
        mock_db = Mock()
        uc = DeleteUploadScopeUseCase(query=fake_port, db=mock_db)

        # Act
        uc.execute(upload_file_id=1, target_date=date(2025, 11, 15), csv_kind="yard")

        # Assert

        assert fake_port.get_deleted_count() == 1

    def test_delete_with_shipment_kind(self):
        """Test delete with 'shipment' kind"""
        # Arrange
        fake_port = FakeUploadStatusQuery()
        mock_db = Mock()
        uc = DeleteUploadScopeUseCase(query=fake_port, db=mock_db)

        # Act
        uc.execute(upload_file_id=1, target_date=date(2025, 11, 15), csv_kind="shipment")

        # Assert

        assert fake_port.get_deleted_count() == 1

    def test_delete_with_shogun_flash_kind(self):
        """Test delete with 'shogun_flash' kind"""
        # Arrange
        fake_port = FakeUploadStatusQuery()
        mock_db = Mock()
        uc = DeleteUploadScopeUseCase(query=fake_port, db=mock_db)

        # Act
        uc.execute(upload_file_id=1, target_date=date(2025, 11, 15), csv_kind="shogun_flash")

        # Assert

        assert fake_port.get_deleted_count() == 1
