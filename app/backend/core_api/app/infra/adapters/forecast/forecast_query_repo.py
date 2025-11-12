"""
Forecast query repository: read-only operations on forecast.predictions_daily.
"""
from typing import List
from datetime import date as date_type
from sqlalchemy.orm import Session

from app.infra.db_models.orm_models import PredictionDaily
from app.domain.models import PredictionDTO


class ForecastQueryRepository:
    """Repository for reading forecast predictions."""

    def __init__(self, db: Session):
        self.db = db

    def list_predictions(self, from_: date_type, to_: date_type) -> List[PredictionDTO]:
        """
        Retrieve predictions within the date range [from_, to_].
        Returns a list of PredictionDTO.
        """
        rows = (
            self.db.query(PredictionDaily)
            .filter(PredictionDaily.date >= from_, PredictionDaily.date <= to_)
            .order_by(PredictionDaily.date)
            .all()
        )
        return [
            PredictionDTO(
                date=row.date,
                y_hat=float(row.y_hat),
                y_lo=float(row.y_lo) if row.y_lo else None,
                y_hi=float(row.y_hi) if row.y_hi else None,
                model_version=row.model_version,
                generated_at=row.generated_at,
            )
            for row in rows
        ]
