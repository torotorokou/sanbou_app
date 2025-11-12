"""
Fake implementations of Domain Ports for testing.
"""
from datetime import date as date_type
from typing import List, Optional, Dict, Any

from app.domain.inbound import InboundDailyRow, CumScope
from app.domain.models import ForecastJobCreate, ForecastJobResponse, PredictionDTO


class FakeDashboardQueryPort:
    """Fake implementation of Dashboard Query Port."""
    
    def __init__(self):
        self._data: Dict[tuple, Optional[Dict[str, Any]]] = {}
    
    def set_data(self, requested_date: date_type, mode: str, data: Optional[Dict[str, Any]]):
        """Set mock data for testing."""
        self._data[(requested_date, mode)] = data
    
    def get_by_date_optimized(
        self,
        target_date: date_type,
        mode: str = "daily"
    ) -> Optional[Dict[str, Any]]:
        """Return pre-configured mock data."""
        return self._data.get((target_date, mode))


class FakeForecastQueryPort:
    """Fake implementation of Forecast Query Port."""
    
    def __init__(self):
        self._predictions: List[PredictionDTO] = []
    
    def set_predictions(self, predictions: List[PredictionDTO]):
        """Set mock predictions for testing."""
        self._predictions = predictions
    
    def list_predictions(self, from_: date_type, to_: date_type) -> List[PredictionDTO]:
        """Return pre-configured mock predictions."""
        return [
            p for p in self._predictions
            if from_ <= p.target_date <= to_
        ]


class FakeJobPort:
    """Fake implementation of Job Port."""
    
    def __init__(self):
        self._jobs: Dict[int, ForecastJobResponse] = {}
        self._next_id = 1
    
    def queue_forecast_job(
        self,
        job_type: str,
        target_from: date_type,
        target_to: date_type,
        actor: str = "system",
        payload_json: Optional[dict] = None,
    ) -> int:
        """Create a fake job and return its ID."""
        job_id = self._next_id
        self._next_id += 1
        
        self._jobs[job_id] = ForecastJobResponse(
            id=job_id,
            job_type=job_type,
            target_from=target_from,
            target_to=target_to,
            status="queued",
            actor=actor,
            payload_json=payload_json,
            created_at=date_type.today(),
            updated_at=date_type.today(),
        )
        return job_id
    
    def get_job_by_id(self, job_id: int) -> Optional[ForecastJobResponse]:
        """Get fake job by ID."""
        return self._jobs.get(job_id)


class FakeInboundQueryPort:
    """Fake implementation of Inbound Query Port."""
    
    def __init__(self):
        self._data: List[InboundDailyRow] = []
    
    def set_data(self, data: List[InboundDailyRow]):
        """Set mock data for testing."""
        self._data = data
    
    def fetch_daily(
        self,
        start: date_type,
        end: date_type,
        segment: Optional[str] = None,
        cum_scope: CumScope = "none"
    ) -> List[InboundDailyRow]:
        """Return pre-configured mock data."""
        return [
            row for row in self._data
            if start <= row.target_date <= end
            and (segment is None or row.segment == segment)
        ]


class FakeExternalApiPort:
    """Fake implementation of External API Port."""
    
    def __init__(self):
        self._rag_responses: Dict[str, dict] = {}
        self._manuals: List[Dict] = []
        self._manual_details: Dict[str, dict] = {}
        self._reports: Dict[tuple, dict] = {}
        self._classifications: Dict[str, dict] = {}
    
    def set_rag_response(self, query: str, response: dict):
        """Set mock RAG response."""
        self._rag_responses[query] = response
    
    async def ask_rag(self, query: str) -> dict:
        """Return pre-configured mock response."""
        return self._rag_responses.get(query, {"answer": "mock answer", "sources": []})
    
    def set_manuals(self, manuals: List[Dict]):
        """Set mock manuals list."""
        self._manuals = manuals
    
    async def list_manuals(self) -> List[Dict]:
        """Return pre-configured mock manuals."""
        return self._manuals
    
    def set_manual(self, manual_id: str, manual: dict):
        """Set mock manual detail."""
        self._manual_details[manual_id] = manual
    
    async def get_manual(self, manual_id: str) -> dict:
        """Return pre-configured mock manual."""
        return self._manual_details.get(manual_id, {})
    
    def set_report(self, report_type: str, params: dict, report: dict):
        """Set mock report."""
        self._reports[(report_type, str(params))] = report
    
    async def generate_report(self, report_type: str, params: dict) -> dict:
        """Return pre-configured mock report."""
        return self._reports.get((report_type, str(params)), {})
    
    def set_classification(self, text: str, classification: dict):
        """Set mock classification."""
        self._classifications[text] = classification
    
    async def classify_text(self, text: str) -> dict:
        """Return pre-configured mock classification."""
        return self._classifications.get(text, {"category": "unknown"})
