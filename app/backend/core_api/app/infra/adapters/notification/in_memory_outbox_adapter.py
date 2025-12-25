"""
InMemory Notification Outbox Adapter

プロセス内メモリで outbox を保持（開発・テスト用）。
将来 DB 化する際はこのファイルを差し替えるか、別クラスに実装。
"""

import threading
from datetime import datetime, timedelta
from uuid import UUID

from app.core.domain.notification import (
    FailureType,
    NotificationOutboxItem,
    NotificationStatus,
)
from app.core.ports.notification_port import NotificationOutboxPort
from backend_shared.application.logging import get_module_logger

logger = get_module_logger(__name__)


class InMemoryNotificationOutboxAdapter(NotificationOutboxPort):
    """
    InMemory Outbox 実装

    - スレッド安全性: 最小限（単一プロセス想定）
    - 永続化なし
    """

    def __init__(self):
        self._items: dict[UUID, NotificationOutboxItem] = {}
        self._lock = threading.Lock()

    def enqueue(self, items: list[NotificationOutboxItem]) -> None:
        """通知アイテムを登録"""
        with self._lock:
            for item in items:
                self._items[item.id] = item
                logger.info(
                    "[Outbox] Enqueued notification",
                    extra={
                        "notification_id": str(item.id),
                        "channel": item.channel,
                        "recipient_key": item.recipient_key,
                        "status": item.status.value,
                    },
                )

    def list_pending(
        self, now: datetime, limit: int = 100
    ) -> list[NotificationOutboxItem]:
        """送信対象の pending アイテムを取得"""
        with self._lock:
            pending = []
            for item in self._items.values():
                if item.status != NotificationStatus.PENDING:
                    continue
                # scheduled_at チェック
                if item.scheduled_at is not None and item.scheduled_at > now:
                    continue
                # next_retry_at チェック
                if item.next_retry_at is not None and item.next_retry_at > now:
                    continue
                pending.append(item)
                if len(pending) >= limit:
                    break

            logger.info(
                f"[Outbox] Found {len(pending)} pending notifications",
                extra={"limit": limit},
            )
            return pending

    def mark_sent(self, id: UUID, sent_at: datetime) -> None:
        """送信成功をマーク"""
        with self._lock:
            if id not in self._items:
                logger.warning(
                    "[Outbox] mark_sent called for unknown id",
                    extra={"notification_id": str(id)},
                )
                return
            item = self._items[id]
            # dataclass は immutable ではないので直接変更
            item.status = NotificationStatus.SENT
            item.sent_at = sent_at
            logger.info(
                "[Outbox] Marked notification as sent",
                extra={"notification_id": str(id), "sent_at": sent_at.isoformat()},
            )

    def mark_failed(
        self, id: UUID, error: str, failure_type: FailureType, now: datetime
    ) -> None:
        """送信失敗をマーク（TEMP/PERM対応）"""
        with self._lock:
            if id not in self._items:
                logger.warning(
                    "[Outbox] mark_failed called for unknown id",
                    extra={"notification_id": str(id)},
                )
                return
            item = self._items[id]
            item.last_error = error
            item.failure_type = failure_type

            if failure_type == FailureType.TEMPORARY:
                # TEMPORARY: pendingに戻してリトライ対象にする
                item.status = NotificationStatus.PENDING
                item.retry_count += 1

                # 簡易バックオフ: 1分, 5分, 30分, それ以降は 60分
                backoff_minutes = {
                    1: 1,
                    2: 5,
                    3: 30,
                }.get(item.retry_count, 60)
                item.next_retry_at = now + timedelta(minutes=backoff_minutes)

                logger.info(
                    "[Outbox] Marked notification as failed (TEMPORARY)",
                    extra={
                        "notification_id": str(id),
                        "retry_count": item.retry_count,
                        "next_retry_at": item.next_retry_at.isoformat(),
                        "error": error[:100],
                    },
                )
            else:
                # PERMANENT: failedのままでリトライしない
                item.status = NotificationStatus.FAILED
                logger.warning(
                    "[Outbox] Marked notification as failed (PERMANENT)",
                    extra={
                        "notification_id": str(id),
                        "error": error[:100],
                    },
                )

    def mark_skipped(self, id: UUID, reason: str, now: datetime) -> None:
        """送信スキップをマーク"""
        with self._lock:
            if id not in self._items:
                logger.warning(
                    "[Outbox] mark_skipped called for unknown id",
                    extra={"notification_id": str(id)},
                )
                return
            item = self._items[id]
            item.status = NotificationStatus.SKIPPED
            item.last_error = reason
            logger.info(
                "[Outbox] Marked notification as skipped",
                extra={
                    "notification_id": str(id),
                    "reason": reason[:100],
                },
            )
