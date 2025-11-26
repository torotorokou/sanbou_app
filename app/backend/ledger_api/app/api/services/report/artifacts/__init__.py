"""
Backward compatibility for artifact management.

新しい場所: app.infra.adapters.artifact_storage
"""

from app.infra.adapters.artifact_storage import (
    get_report_artifact_storage,
    ReportArtifactStorage,
)
from app.infra.adapters.artifact_storage import (
    ArtifactResponseBuilder,
)
)

__all__ = [
    "get_report_artifact_storage",
    "ReportArtifactStorage",
    "ArtifactResponseBuilder",
]
