"""
Domain Layer

ビジネスドメインモデル（Entity, 値オブジェクト, ドメインサービス）。
外部 I/O (DB, HTTP, 設定) には依存しない純粋なビジネスロジック。

このレイヤーは:
- 業務ルール・不変条件を表現する
- 外部依存（DB, HTTP, フレームワーク）を持たない
- 他のレイヤーから依存される（依存関係逆転の原則）
"""

from backend_shared.core.domain.contract import (
    NotificationEvent,
    ProblemDetails,
    Severity,
)
from backend_shared.core.domain.job import (
    JobCreate,
    JobStatus,
    JobStatusType,
    JobUpdate,
)

__all__ = [
    "ProblemDetails",
    "NotificationEvent",
    "Severity",
    "JobStatus",
    "JobCreate",
    "JobUpdate",
    "JobStatusType",
]
