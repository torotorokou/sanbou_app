"""
Ingest service: handles CSV upload and reservation logic.
"""
from typing import List
from datetime import date as date_type
from sqlalchemy.orm import Session

from app.repositories.core_repo import CoreRepository
from app.domain.models import ReservationCreate, ReservationResponse


class IngestService:
    """Service for ingesting data (CSV, reservations)."""

    def __init__(self, db: Session):
        self.repo = CoreRepository(db)

    def upload_csv(self, rows: List[dict]) -> dict:
        """
        Process and store CSV data.
        TODO: Define CSV column spec and validation.
        Expected columns: date, trucks, weight, vendor, etc.
        """
        # TODO: Validate CSV schema
        # TODO: Parse and normalize data
        self.repo.upsert_actuals(rows)
        return {"status": "success", "rows_inserted": len(rows)}

    def create_reservation(self, req: ReservationCreate) -> ReservationResponse:
        """Create or update a truck reservation."""
        reservation = self.repo.insert_reservation(date=req.date, trucks=req.trucks)
        return ReservationResponse(
            date=reservation.date,
            trucks=reservation.trucks,
            created_at=reservation.created_at,
        )
