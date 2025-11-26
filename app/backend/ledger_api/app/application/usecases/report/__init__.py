"""
Report generation use cases.

Report generation business logic including generators and processors.
"""

from app.application.usecases.report.base_generators import (
    BaseReportGenerator,
    BaseInteractiveReportGenerator,
)
from app.application.usecases.report.processors import (
    ReportProcessingService,
    InteractiveReportProcessingService,
)

# Note: concrete_generators imports are avoided here to prevent circular imports
# Import them directly where needed instead

__all__ = [
    "BaseReportGenerator",
    "BaseInteractiveReportGenerator",
    "ReportProcessingService",
    "InteractiveReportProcessingService",
]
