"""
Core repository: operations on core schema (inbound_actuals, inbound_reservations).
"""
from typing import List
from datetime import date as date_type, datetime
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.repositories.orm_models import InboundActual, InboundReservation


class CoreRepository:
    """Repository for core schema data operations."""

    def __init__(self, db: Session):
        self.db = db

    def upsert_actuals(self, rows: List[dict]) -> None:
        """
        Upsert CSV data into inbound_actuals.
        TODO: Define proper columns based on CSV spec.
        For now, stores flexible JSON.
        """
        for row in rows:
            actual = InboundActual(
                date=row.get("date"),
                data_json=row,
                created_at=datetime.utcnow(),
            )
            self.db.merge(actual)  # Simple upsert via merge
        self.db.flush()

    def insert_reservation(self, date: date_type, trucks: int) -> InboundReservation:
        """
        Insert or update a truck reservation.
        Uses PostgreSQL UPSERT (ON CONFLICT DO UPDATE).
        """
        stmt = pg_insert(InboundReservation).values(
            date=date,
            trucks=trucks,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["date"],
            set_={"trucks": trucks, "updated_at": datetime.utcnow()},
        )
        self.db.execute(stmt)
        self.db.flush()

        # Return the created/updated record
        return self.db.query(InboundReservation).filter(InboundReservation.date == date).first()
