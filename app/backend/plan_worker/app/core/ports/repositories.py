from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Iterable


# domainの型に近い最小DTO（必要最小限）
@dataclass(frozen=True)
class DayTypeStatDTO:
    day_type: str
    sample_days: int
    mean_ton: Decimal


@dataclass(frozen=True)
class DayTypeRatioDTO:
    day_type: str
    mean_ton: Decimal
    ratio: Decimal
    sample_days: int | None = None


class ActualsRepository:
    def fetch_daytype_stats(
        self, window_start: date, window_end: date, lookback_years: int
    ) -> Iterable[DayTypeStatDTO]:
        raise NotImplementedError


class RatiosRepository:
    def upsert_ratios(
        self,
        effective_from: date,
        ratios: Iterable[DayTypeRatioDTO],
        lookback_years: int,
    ) -> None:
        raise NotImplementedError
