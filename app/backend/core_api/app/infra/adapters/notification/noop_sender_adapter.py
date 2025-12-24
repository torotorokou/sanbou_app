"""
Noop Notification Sender Adapter

実際の送信を行わず、ログ出力のみ（開発・テスト用）。
将来、実送信実装（email SDK, LINE API 等）に差し替える。
"""
from backend_shared.application.logging import get_module_logger

from app.core.domain.notification import NotificationChannel, NotificationPayload
from app.core.ports.notification_port import NotificationSenderPort

logger = get_module_logger(__name__)


class NoopNotificationSenderAdapter(NotificationSenderPort):
    """
    No-op Sender 実装
    
    外部API呼び出しは行わず、ログ出力のみ。
    将来的に実装を差し替える。
    """

    def send(
        self,
        channel: NotificationChannel,
        payload: NotificationPayload,
        recipient_key: str,
    ) -> None:
        """通知を「送信」（実際はログ出力のみ）"""
        logger.info(
            f"[NOOP][{channel}] Notification sent (noop)",
            extra={
                "channel": channel,
                "recipient_key": recipient_key,
                "title": payload.title,
                "body": payload.body[:50],  # 最初の50文字
                "url": payload.url,
                "meta": payload.meta,
            },
        )
        # 正常終了（例外を投げない = 成功扱い）
