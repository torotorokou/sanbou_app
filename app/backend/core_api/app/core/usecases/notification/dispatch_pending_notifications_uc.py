"""
Dispatch Pending Notifications UseCase

Outbox から pending 通知を取り出し、Sender で送信するユースケース。

処理フロー:
1. outbox.list_pending で対象を取得
2. 各itemについて:
   a) preference判定（通知許可チェック）
   b) resolver でチャネル固有IDに解決
   c) sender.send で送信
   d) 成功/失敗で状態を更新
"""
from datetime import datetime
from typing import Optional

from backend_shared.application.logging import get_module_logger

from app.core.domain.notification import FailureType, RecipientRef
from app.core.ports.notification_port import (
    NotificationOutboxPort,
    NotificationPreferencePort,
    NotificationSenderPort,
    RecipientResolverPort,
)

logger = get_module_logger(__name__)


class DispatchPendingNotificationsUseCase:
    """
    pending 通知を送信
    
    - preference で通知許可をチェック
    - resolver でチャネル固有IDに解決
    - sender.send で送信（成功/失敗で状態を更新）
    - TEMP失敗: リトライ対象
    - PERM失敗: skipped または failed（リトライなし）
    """

    def __init__(
        self,
        outbox: NotificationOutboxPort,
        sender: NotificationSenderPort,
        preference: Optional[NotificationPreferencePort] = None,
        resolver: Optional[RecipientResolverPort] = None,
    ):
        self._outbox = outbox
        self._sender = sender
        self._preference = preference
        self._resolver = resolver

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
                # Step 1: Preference判定（user: のみ、email:/aud: は常に許可）
                recipient_ref = RecipientRef.parse(item.recipient_key)
                if recipient_ref and recipient_ref.kind == "user" and self._preference:
                    pref = self._preference.get_for_recipient(item.recipient_key)
                    if pref:
                        # チャネル別の許可チェック
                        if item.channel == "line" and not pref.line_enabled:
                            self._outbox.mark_skipped(
                                id=item.id,
                                reason=f"LINE notification disabled for {item.recipient_key}",
                                now=now,
                            )
                            logger.info(
                                f"Skipped: LINE disabled",
                                extra={
                                    "notification_id": str(item.id),
                                    "recipient_key": item.recipient_key,
                                },
                            )
                            continue
                        elif item.channel == "email" and not pref.email_enabled:
                            self._outbox.mark_skipped(
                                id=item.id,
                                reason=f"Email notification disabled for {item.recipient_key}",
                                now=now,
                            )
                            logger.info(
                                f"Skipped: Email disabled",
                                extra={
                                    "notification_id": str(item.id),
                                    "recipient_key": item.recipient_key,
                                },
                            )
                            continue

                # Step 2: Resolver で解決
                resolved_to = item.recipient_key  # デフォルトはそのまま
                if self._resolver:
                    resolved = self._resolver.resolve(item.recipient_key, item.channel)
                    if resolved is None:
                        # 解決不可 → PERMANENT失敗でskipped
                        self._outbox.mark_skipped(
                            id=item.id,
                            reason=f"Recipient not resolved for channel={item.channel}",
                            now=now,
                        )
                        logger.warning(
                            f"Skipped: Recipient not resolved",
                            extra={
                                "notification_id": str(item.id),
                                "recipient_key": item.recipient_key,
                                "channel": item.channel,
                            },
                        )
                        continue
                    resolved_to = resolved

                # Step 3: 送信
                self._sender.send(
                    channel=item.channel,
                    payload=item.payload,
                    recipient_key=resolved_to,
                )
                self._outbox.mark_sent(id=item.id, sent_at=now)
                sent_count += 1

            except ValueError as e:
                # ValueError → PERMANENT失敗
                error_msg = f"{type(e).__name__}: {str(e)}"
                logger.warning(
                    f"PERMANENT failure (ValueError)",
                    extra={
                        "notification_id": str(item.id),
                        "channel": item.channel,
                        "error": error_msg,
                    },
                )
                self._outbox.mark_failed(
                    id=item.id,
                    error=error_msg,
                    failure_type=FailureType.PERMANENT,
                    now=now,
                )

            except Exception as e:
                # その他の例外 → TEMPORARY失敗（リトライ）
                error_msg = f"{type(e).__name__}: {str(e)}"
                logger.warning(
                    f"TEMPORARY failure (will retry)",
                    extra={
                        "notification_id": str(item.id),
                        "channel": item.channel,
                        "error": error_msg,
                    },
                )
                self._outbox.mark_failed(
                    id=item.id,
                    error=error_msg,
                    failure_type=FailureType.TEMPORARY,
                    now=now,
                )

        logger.info(
            f"Dispatched {sent_count}/{len(pending_items)} notifications",
            extra={"sent": sent_count, "total": len(pending_items)},
        )
        return sent_count
