"""
Dummy predictor for forecast worker.
TODO: Replace with real ML model.
"""
from datetime import date as date_type, timedelta
from typing import List, Dict
import random


class Predictor:
    """
    Dummy predictor that generates fake predictions.
    TODO: Integrate with real Prophet/ML model.
    """

    def __init__(self):
        self.model_version = "dummy_v1.0"

    def predict(self, from_date: date_type, to_date: date_type) -> List[Dict]:
        """
        Generate predictions for date range.
        Returns list of dicts: {date, y_hat, y_lo, y_hi}
        """
        predictions = []
        current = from_date
        while current <= to_date:
            y_hat = 100 + random.uniform(-10, 10)
            predictions.append({
                "date": current,
                "y_hat": round(y_hat, 2),
                "y_lo": round(y_hat - 5, 2),
                "y_hi": round(y_hat + 5, 2),
                "model_version": self.model_version,
            })
            current += timedelta(days=1)
        return predictions
