"""Endpoints package initializer.

DEPRECATED: This module is deprecated. Use app.presentation.api.routers instead.
"""

# Backward compatibility imports
from app.presentation.api.routers.report_artifacts import router as report_artifact_router  # noqa: F401
from app.presentation.api.routers.reports import reports_router  # noqa: F401

__all__ = ["reports_router", "report_artifact_router"]
