"""
Backward compatibility for core report components.

新しい場所: app.application.usecases.report
"""

from app.application.usecases.report import (
    BaseReportGenerator,
    BaseInteractiveReportGenerator,
)
from app.application.usecases.report import (
    ReportProcessingService,
    InteractiveReportProcessingService,
)

__all__ = [
    # Base generators
    "BaseReportGenerator",
    "BaseInteractiveReportGenerator",
    # Processors
    "ReportProcessingService",
    "InteractiveReportProcessingService",
]
