"""
Smoke test for backend_shared package
"""


def test_import():
    """backend_shared パッケージがインポートできることを確認"""
    import importlib
    
    m = importlib.import_module("backend_shared")
    assert m is not None
    assert hasattr(m, "__version__")


def test_domain_import():
    """domain モジュールがインポートできることを確認"""
    from backend_shared.domain import JobStatus, NotificationEvent, ProblemDetails
    
    assert JobStatus is not None
    assert NotificationEvent is not None
    assert ProblemDetails is not None
