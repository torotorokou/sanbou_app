"""
Domain契約モジュール

通知契約モデル（OpenAPI準拠）のエクスポート
"""

from .contract import ProblemDetails, NotificationEvent, Severity
from .job import JobStatus, JobCreate, JobUpdate, JobStatusType

__all__ = [
    "ProblemDetails",
    "NotificationEvent",
    "Severity",
    "JobStatus",
    "JobCreate",
    "JobUpdate",
    "JobStatusType",
]
