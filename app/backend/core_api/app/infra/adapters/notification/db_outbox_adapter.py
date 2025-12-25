"""
DB-backed NotificationOutbox adapter implementation.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List
from uuid import UUID, uuid4

from app.core.domain.notification import (
    FailureType,
    NotificationChannel,
    NotificationOutboxItem,
    NotificationPayload,
    NotificationStatus,
)
from app.core.ports.notification_port import NotificationOutboxPort
from app.infra.db.orm_models import NotificationOutboxORM
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class DbNotificationOutboxAdapter(NotificationOutboxPort):
    """PostgreSQL database-backed notification outbox implementation."""

    def __init__(self, db: Session):
        self.db = db

    def enqueue(self, items: List[NotificationOutboxItem]) -> None:
        """通知をOutboxに追加"""
        for item in items:
            orm_item = NotificationOutboxORM(
                id=item.id,
                channel=item.channel,
                status=item.status.value,
                recipient_key=item.recipient_key,
                title=item.payload.title,
                body=item.payload.body,
                url=item.payload.url,
                meta=item.payload.meta,
                scheduled_at=item.scheduled_at,
                created_at=item.created_at,
                sent_at=item.sent_at,
                retry_count=item.retry_count,
                next_retry_at=item.next_retry_at,
                last_error=item.last_error,
                failure_type=item.failure_type.value if item.failure_type else None,
            )
            self.db.add(orm_item)

        self.db.commit()
        logger.info(f"Enqueued {len(items)} notifications to DB")

    def list_pending(
        self, now: datetime, limit: int = 100
    ) -> List[NotificationOutboxItem]:
        """送信待ちの通知を取得"""

        # ステータスがpendingで、scheduled_atが過去または未設定、next_retry_atが過去または未設定
        orm_items = (
            self.db.query(NotificationOutboxORM)
            .filter(
                NotificationOutboxORM.status == NotificationStatus.PENDING.value,
                (NotificationOutboxORM.scheduled_at.is_(None))
                | (NotificationOutboxORM.scheduled_at <= now),
                (NotificationOutboxORM.next_retry_at.is_(None))
                | (NotificationOutboxORM.next_retry_at <= now),
            )
            .order_by(NotificationOutboxORM.created_at)
            .limit(limit)
            .all()
        )

        return [self._to_domain(orm_item) for orm_item in orm_items]

    def mark_sent(self, id: UUID, sent_at: datetime) -> None:
        """通知を送信済みにマーク"""
        orm_item = self.db.query(NotificationOutboxORM).filter_by(id=id).first()
        if not orm_item:
            logger.warning(f"Notification {id} not found for mark_sent")
            return

        orm_item.status = NotificationStatus.SENT.value
        orm_item.sent_at = sent_at
        self.db.commit()
        logger.info(f"Marked notification {id} as sent")

    def mark_failed(
        self, id: UUID, error: str, failure_type: FailureType, now: datetime
    ) -> None:
        """通知を失敗にマーク（TEMPORARY: リトライ、PERMANENT: 即失敗）"""
        orm_item = self.db.query(NotificationOutboxORM).filter_by(id=id).first()
        if not orm_item:
            logger.warning(f"Notification {id} not found for mark_failed")
            return

        orm_item.last_error = error
        orm_item.failure_type = failure_type.value

        if failure_type == FailureType.PERMANENT:
            # PERMANENT: 即座に failed に遷移（リトライなし）
            orm_item.status = NotificationStatus.FAILED.value
            orm_item.next_retry_at = None
            logger.error(f"Notification {id} permanently failed: {error}")
        else:
            # TEMPORARY: リトライ対象
            orm_item.retry_count += 1

            # Exponential backoff: 1min, 5min, 30min, 1hour
            backoff_minutes = [1, 5, 30, 60]
            max_retries = len(backoff_minutes)

            if orm_item.retry_count < max_retries:
                orm_item.status = NotificationStatus.PENDING.value
                delay_minutes = backoff_minutes[orm_item.retry_count - 1]
                orm_item.next_retry_at = now + timedelta(minutes=delay_minutes)
                logger.info(
                    f"Notification {id} failed temporarily (retry {orm_item.retry_count}/{max_retries}), "
                    f"will retry in {delay_minutes}min"
                )
            else:
                orm_item.status = NotificationStatus.FAILED.value
                orm_item.next_retry_at = None
                logger.error(
                    f"Notification {id} permanently failed after {max_retries} retries"
                )

        self.db.commit()

    def mark_skipped(self, id: UUID, reason: str, now: datetime) -> None:
        """通知をスキップにマーク（送信不要）"""
        orm_item = self.db.query(NotificationOutboxORM).filter_by(id=id).first()
        if not orm_item:
            logger.warning(f"Notification {id} not found for mark_skipped")
            return

        orm_item.status = NotificationStatus.SKIPPED.value
        orm_item.last_error = reason
        self.db.commit()
        logger.info(f"Skipped notification {id}: {reason}")

    def _to_domain(self, orm_item: NotificationOutboxORM) -> NotificationOutboxItem:
        """ORMモデルをドメインモデルに変換"""
        payload = NotificationPayload(
            title=orm_item.title,
            body=orm_item.body,
            url=orm_item.url,
            meta=orm_item.meta,
        )
        return NotificationOutboxItem(
            id=orm_item.id,
            channel=orm_item.channel,
            status=NotificationStatus(orm_item.status),
            recipient_key=orm_item.recipient_key,
            payload=payload,
            scheduled_at=orm_item.scheduled_at,
            created_at=orm_item.created_at,
            sent_at=orm_item.sent_at,
            retry_count=orm_item.retry_count,
            next_retry_at=orm_item.next_retry_at,
            last_error=orm_item.last_error,
            failure_type=(
                FailureType(orm_item.failure_type) if orm_item.failure_type else None
            ),
        )
