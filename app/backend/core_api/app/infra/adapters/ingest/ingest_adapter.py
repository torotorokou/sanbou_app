"""
Ingest Adapter: Implements IngestPort for data ingestion operations.
"""

from datetime import date as date_type
from typing import List

from app.infra.adapters.misc.core_repository import CoreRepository
from sqlalchemy.orm import Session


class IngestAdapter:
    """
    Adapter for data ingestion operations.
    Implements the ingest port interface.
    """

    def __init__(self, db: Session):
        self._repo = CoreRepository(db)

    def upsert_actuals(self, rows: List[dict]) -> None:
        """Insert or update actual data rows."""
        self._repo.upsert_actuals(rows)

    def insert_reservation(self, date: date_type, trucks: int) -> dict:
        """Insert a truck reservation."""
        reservation = self._repo.insert_reservation(date=date, trucks=trucks)
        return {
            "date": reservation.date,
            "trucks": reservation.trucks,
            "created_at": reservation.created_at,
        }
