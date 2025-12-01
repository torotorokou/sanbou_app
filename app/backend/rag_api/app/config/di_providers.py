from functools import lru_cache
from app.core.ports.manuals.manuals_repository import ManualsRepository
from app.infra.adapters.manuals.manuals_repository import InMemoryManualRepository
from app.core.usecases.manuals.manuals_service import ManualsService
from app.core.ports.rag.pdf_service_port import PDFServiceBase
from app.infra.adapters.rag.pdf_service_adapter import PDFService
from app.core.usecases.rag.ai_response_service import AIResponseService
from app.core.usecases.rag.dummy_response_service import DummyResponseService

@lru_cache
def get_manuals_repository() -> ManualsRepository:
    return InMemoryManualRepository()

def get_manuals_service() -> ManualsService:
    return ManualsService(repo=get_manuals_repository())

@lru_cache
def get_pdf_service() -> PDFServiceBase:
    return PDFService()

def get_ai_response_service() -> AIResponseService:
    return AIResponseService(pdf_service=get_pdf_service())

def get_dummy_response_service() -> DummyResponseService:
    return DummyResponseService(pdf_service=get_pdf_service())
