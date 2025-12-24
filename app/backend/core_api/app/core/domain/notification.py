"""
Notification Domain Models

外部依存ゼロ。通知の型・不変条件を定義。
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Literal, Optional
from uuid import UUID, uuid4


# 通知チャネル（将来拡張可能）
NotificationChannel = Literal["email", "line", "webhook", "push"]


class NotificationStatus(str, Enum):
    """通知ステータス"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class NotificationPayload:
    """通知ペイロード（チャネル共通の最小構造）"""
    title: str
    body: str
    url: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """不変条件チェック"""
        if not self.title.strip():
            raise ValueError("title must not be empty")
        if not self.body.strip():
            raise ValueError("body must not be empty")


@dataclass
class NotificationOutboxItem:
    """
    通知 Outbox アイテム
    
    - enqueue 時に作成
    - dispatch で処理され、sent/failed に遷移
    - 失敗時は retry_count と next_retry_at で再試行制御
    """
    id: UUID
    channel: NotificationChannel
    status: NotificationStatus
    payload: NotificationPayload
    recipient_key: str  # user_id、audience キー等
    created_at: datetime
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    retry_count: int = 0
    next_retry_at: Optional[datetime] = None
    last_error: Optional[str] = None

    def __post_init__(self):
        """不変条件チェック"""
        if not self.recipient_key.strip():
            raise ValueError("recipient_key must not be empty")
        if self.retry_count < 0:
            raise ValueError("retry_count must be non-negative")

    @staticmethod
    def create_pending(
        channel: NotificationChannel,
        payload: NotificationPayload,
        recipient_key: str,
        now: datetime,
        scheduled_at: Optional[datetime] = None,
    ) -> "NotificationOutboxItem":
        """pending 状態の新規アイテムを作成"""
        return NotificationOutboxItem(
            id=uuid4(),
            channel=channel,
            status=NotificationStatus.PENDING,
            payload=payload,
            recipient_key=recipient_key,
            created_at=now,
            scheduled_at=scheduled_at,
        )
