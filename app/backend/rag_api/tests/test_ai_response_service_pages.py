from app.core.usecases.ai_response_service import AIResponseService
from app.core.ports.pdf_service_port import PDFServiceBase


class _DummyPDFService(PDFServiceBase):
    def save_pdf_pages_and_get_urls(self, *args, **kwargs):
        raise NotImplementedError

    def merge_pdfs(self, *args, **kwargs):
        raise NotImplementedError


def _svc():
    return AIResponseService(pdf_service=_DummyPDFService())


def test_normalize_pages_simple_comma_and_range():
    svc = _svc()
    assert svc._normalize_pages("1,2-4,7") == [1, 2, 3, 4, 7]


def test_normalize_pages_list_with_mixed_tokens():
    svc = _svc()
    assert svc._normalize_pages(["1", "3-5", "8,10-11"]) == [1, 3, 4, 5, 8, 10, 11]


def test_normalize_pages_invalid_and_desc_range():
    svc = _svc()
    assert svc._normalize_pages("invalid,3-2, 6") == [6]


def test_normalize_pages_none():
    svc = _svc()
    assert svc._normalize_pages(None) == []
