"""Endpoints package initializer.

Strict import: ここで失敗すれば起動前に即座に異常を検知できる。
"""

from . import manage_report  # noqa: F401
from .report_artifacts import router as report_artifact_router  # noqa: F401
from .reports import reports_router  # noqa: F401

__all__ = ["reports_router", "manage_report", "report_artifact_router"]
