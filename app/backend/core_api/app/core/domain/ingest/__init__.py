"""
Ingest domain package.
データ取り込み（搬入予約）のドメインモデル
"""
from app.core.domain.ingest.entities import (
    ReservationCreate,
    ReservationResponse,
)

__all__ = [
    "ReservationCreate",
    "ReservationResponse",
]
