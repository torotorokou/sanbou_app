"""
Dispatch Pending Notifications UseCase

Outbox から pending 通知を取り出し、Sender で送信するユースケース。
"""
from datetime import datetime

from backend_shared.application.logging import get_module_logger

from app.core.ports.notification_port import (
    NotificationOutboxPort,
    NotificationSenderPort,
)

logger = get_module_logger(__name__)


class DispatchPendingNotificationsUseCase:
    """
    pending 通知を送信
    
    - outbox.list_pending で対象を取得
    - sender.send で送信（成功/失敗で状態を更新）
    - 1件ずつ処理（並列化は将来検討）
    """

    def __init__(self, outbox: NotificationOutboxPort, sender: NotificationSenderPort):
        self._outbox = outbox
        self._sender = sender

    def execute(self, now: datetime, limit: int = 100) -> int:
        """
        pending 通知を送信
        
        Args:
            now: 現在時刻
            limit: 1回の実行で処理する最大件数
            
        Returns:
            送信成功件数
        """
        pending_items = self._outbox.list_pending(now=now, limit=limit)
        if not pending_items:
            logger.info("No pending notifications to dispatch")
            return 0

        sent_count = 0
        for item in pending_items:
            try:
                self._sender.send(
                    channel=item.channel,
                    payload=item.payload,
                    recipient_key=item.recipient_key,
                )
                self._outbox.mark_sent(id=item.id, sent_at=now)
                sent_count += 1
            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                logger.warning(
                    f"Failed to send notification",
                    extra={
                        "notification_id": str(item.id),
                        "channel": item.channel,
                        "error": error_msg,
                    },
                )
                self._outbox.mark_failed(id=item.id, error=error_msg, now=now)

        logger.info(
            f"Dispatched {sent_count}/{len(pending_items)} notifications",
            extra={"sent": sent_count, "total": len(pending_items)},
        )
        return sent_count
