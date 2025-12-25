"""
Enqueue Notifications UseCase

通知要求を Outbox に登録するユースケース。
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from app.core.domain.notification import (
    NotificationChannel,
    NotificationOutboxItem,
    NotificationPayload,
)
from app.core.ports.notification_port import NotificationOutboxPort
from backend_shared.application.logging import get_module_logger

logger = get_module_logger(__name__)


@dataclass(frozen=True)
class EnqueueNotificationRequest:
    """通知登録リクエスト"""

    channel: NotificationChannel
    title: str
    body: str
    recipient_key: str
    url: Optional[str] = None
    scheduled_at: Optional[datetime] = None


class EnqueueNotificationsUseCase:
    """
    通知を Outbox に登録

    - 複数の通知を一括登録可能
    - created_at は UseCase 側で補完
    """

    def __init__(self, outbox: NotificationOutboxPort):
        self._outbox = outbox

    def execute(
        self, requests: List[EnqueueNotificationRequest], now: datetime
    ) -> None:
        """
        通知を Outbox に登録

        Args:
            requests: 登録する通知リクエスト
            now: 現在時刻（テストで差し替え可能にするため注入）
        """
        items: List[NotificationOutboxItem] = []
        for req in requests:
            payload = NotificationPayload(
                title=req.title,
                body=req.body,
                url=req.url,
            )
            item = NotificationOutboxItem.create_pending(
                channel=req.channel,
                payload=payload,
                recipient_key=req.recipient_key,
                now=now,
                scheduled_at=req.scheduled_at,
            )
            items.append(item)

        self._outbox.enqueue(items)
        logger.info(f"Enqueued {len(items)} notifications", extra={"count": len(items)})
