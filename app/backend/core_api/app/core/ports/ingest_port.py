"""
Ingest Port: Interface for data ingestion operations.
"""
from typing import Protocol, List, Dict
from datetime import date as date_type


class IngestPort(Protocol):
    """Port for data ingestion operations (CSV upload, reservations)."""
    
    def upsert_actuals(self, rows: List[dict]) -> None:
        """Insert or update actual data rows."""
        ...
    
    def insert_reservation(self, date: date_type, trucks: int) -> dict:
        """Insert a truck reservation."""
        ...
