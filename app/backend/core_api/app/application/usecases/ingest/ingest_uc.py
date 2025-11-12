"""
Ingest UseCase: Handles CSV upload and truck reservations.

TODO: 将来的にPort&Adapter化予定
  - 現在はSession直接利用
  - 今後、UploadIngestCsvUseCase, CreateReservationUseCase に分割
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime

from app.domain.models import ReservationCreate, ReservationResponse


class IngestUseCase:
    """UseCase for data ingestion operations."""

    def __init__(self, db: Session):
        self.db = db

    def upload_csv(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process uploaded CSV data.
        
        TODO: Implement actual data processing and DB insertion
        Currently returns a simple success response.
        """
        # TODO: Validate and insert rows into database
        # For now, just return success
        return {
            "success": True,
            "rows_processed": len(rows),
            "message": "CSV upload completed (stub implementation)"
        }

    def create_reservation(self, req: ReservationCreate) -> ReservationResponse:
        """
        Create or update a truck reservation.
        
        TODO: Implement actual reservation logic
        Currently returns a stub response.
        """
        # TODO: Insert/update reservation in database
        # For now, return a stub response
        return ReservationResponse(
            date=req.date,
            trucks=req.trucks,
            created_at=datetime.utcnow()
        )
