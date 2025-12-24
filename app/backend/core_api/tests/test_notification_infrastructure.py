"""
Notification Infrastructure Tests

通知基盤の動作確認テスト（InMemory/Noop）
"""
from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from app.core.domain.notification import (
    NotificationChannel,
    NotificationOutboxItem,
    NotificationPayload,
    NotificationStatus,
)
from app.core.usecases.notification.enqueue_notifications_uc import (
    EnqueueNotificationRequest,
    EnqueueNotificationsUseCase,
)
from app.core.usecases.notification.dispatch_pending_notifications_uc import (
    DispatchPendingNotificationsUseCase,
)
from app.infra.adapters.notification.in_memory_outbox_adapter import (
    InMemoryNotificationOutboxAdapter,
)
from app.infra.adapters.notification.noop_sender_adapter import (
    NoopNotificationSenderAdapter,
)


@pytest.fixture
def outbox():
    """InMemory Outbox"""
    return InMemoryNotificationOutboxAdapter()


@pytest.fixture
def sender():
    """Noop Sender"""
    return NoopNotificationSenderAdapter()


@pytest.fixture
def enqueue_uc(outbox):
    """Enqueue UseCase"""
    return EnqueueNotificationsUseCase(outbox=outbox)


@pytest.fixture
def dispatch_uc(outbox, sender):
    """Dispatch UseCase"""
    return DispatchPendingNotificationsUseCase(outbox=outbox, sender=sender)


class TestNotificationDomain:
    """Domain 層のテスト"""

    def test_create_notification_payload(self):
        """NotificationPayload の作成"""
        payload = NotificationPayload(
            title="Test Title",
            body="Test Body",
            url="https://example.com",
        )
        assert payload.title == "Test Title"
        assert payload.body == "Test Body"
        assert payload.url == "https://example.com"

    def test_payload_requires_nonempty_title(self):
        """title が空の場合はエラー"""
        with pytest.raises(ValueError, match="title must not be empty"):
            NotificationPayload(title="", body="Body")

    def test_payload_requires_nonempty_body(self):
        """body が空の場合はエラー"""
        with pytest.raises(ValueError, match="body must not be empty"):
            NotificationPayload(title="Title", body="   ")

    def test_create_pending_outbox_item(self):
        """pending アイテムの作成"""
        now = datetime.now()
        payload = NotificationPayload(title="Title", body="Body")
        item = NotificationOutboxItem.create_pending(
            channel="email",
            payload=payload,
            recipient_key="user_123",
            now=now,
        )
        assert item.status == NotificationStatus.PENDING
        assert item.channel == "email"
        assert item.recipient_key == "user_123"
        assert item.created_at == now
        assert item.retry_count == 0


class TestInMemoryOutboxAdapter:
    """InMemory Outbox Adapter のテスト"""

    def test_enqueue_and_list_pending(self, outbox):
        """enqueue して list_pending で取得できる"""
        now = datetime.now()
        payload = NotificationPayload(title="Title", body="Body")
        item = NotificationOutboxItem.create_pending(
            channel="email",
            payload=payload,
            recipient_key="user_123",
            now=now,
        )
        outbox.enqueue([item])

        pending = outbox.list_pending(now=now)
        assert len(pending) == 1
        assert pending[0].id == item.id

    def test_list_pending_respects_scheduled_at(self, outbox):
        """scheduled_at が未来の場合は取得されない"""
        now = datetime.now()
        future = now + timedelta(hours=1)
        payload = NotificationPayload(title="Title", body="Body")
        item = NotificationOutboxItem.create_pending(
            channel="email",
            payload=payload,
            recipient_key="user_123",
            now=now,
            scheduled_at=future,
        )
        outbox.enqueue([item])

        # 現在時刻では取得されない
        pending = outbox.list_pending(now=now)
        assert len(pending) == 0

        # 未来時刻では取得される
        pending = outbox.list_pending(now=future)
        assert len(pending) == 1

    def test_mark_sent(self, outbox):
        """mark_sent で sent 状態になる"""
        now = datetime.now()
        payload = NotificationPayload(title="Title", body="Body")
        item = NotificationOutboxItem.create_pending(
            channel="email",
            payload=payload,
            recipient_key="user_123",
            now=now,
        )
        outbox.enqueue([item])
        outbox.mark_sent(id=item.id, sent_at=now)

        pending = outbox.list_pending(now=now)
        assert len(pending) == 0  # sent なので pending には含まれない

    def test_mark_failed(self, outbox):
        """mark_failed で retry_count と next_retry_at が設定される"""
        now = datetime.now()
        payload = NotificationPayload(title="Title", body="Body")
        item = NotificationOutboxItem.create_pending(
            channel="email",
            payload=payload,
            recipient_key="user_123",
            now=now,
        )
        outbox.enqueue([item])
        outbox.mark_failed(id=item.id, error="Test error", now=now)

        # 現在時刻では next_retry_at が未来なので取得されない
        pending = outbox.list_pending(now=now)
        assert len(pending) == 0

        # 未来時刻（1分後）では取得される
        future = now + timedelta(minutes=2)
        pending = outbox.list_pending(now=future)
        assert len(pending) == 1
        assert pending[0].retry_count == 1
        assert pending[0].last_error == "Test error"


class TestEnqueueNotificationsUseCase:
    """Enqueue UseCase のテスト"""

    def test_enqueue_single_notification(self, enqueue_uc, outbox):
        """1件の通知を登録"""
        now = datetime.now()
        requests = [
            EnqueueNotificationRequest(
                channel="email",
                title="Test Title",
                body="Test Body",
                recipient_key="user_123",
                url="https://example.com",
            )
        ]
        enqueue_uc.execute(requests=requests, now=now)

        pending = outbox.list_pending(now=now)
        assert len(pending) == 1
        assert pending[0].payload.title == "Test Title"

    def test_enqueue_multiple_notifications(self, enqueue_uc, outbox):
        """複数の通知を一括登録"""
        now = datetime.now()
        requests = [
            EnqueueNotificationRequest(
                channel="email",
                title=f"Title {i}",
                body=f"Body {i}",
                recipient_key=f"user_{i}",
            )
            for i in range(5)
        ]
        enqueue_uc.execute(requests=requests, now=now)

        pending = outbox.list_pending(now=now)
        assert len(pending) == 5


class TestDispatchPendingNotificationsUseCase:
    """Dispatch UseCase のテスト"""

    def test_dispatch_success(self, dispatch_uc, outbox):
        """送信成功（Noop）"""
        now = datetime.now()
        payload = NotificationPayload(title="Title", body="Body")
        item = NotificationOutboxItem.create_pending(
            channel="email",
            payload=payload,
            recipient_key="user_123",
            now=now,
        )
        outbox.enqueue([item])

        sent_count = dispatch_uc.execute(now=now)
        assert sent_count == 1

        # sent なので pending には含まれない
        pending = outbox.list_pending(now=now)
        assert len(pending) == 0

    def test_dispatch_with_sender_failure(self, outbox):
        """Sender が例外を投げる場合、failed になる"""
        now = datetime.now()
        payload = NotificationPayload(title="Title", body="Body")
        item = NotificationOutboxItem.create_pending(
            channel="email",
            payload=payload,
            recipient_key="user_123",
            now=now,
        )
        outbox.enqueue([item])

        # 例外を投げる Sender を用意
        failing_sender = Mock()
        failing_sender.send.side_effect = RuntimeError("Test failure")

        dispatch_uc = DispatchPendingNotificationsUseCase(
            outbox=outbox, sender=failing_sender
        )
        sent_count = dispatch_uc.execute(now=now)
        assert sent_count == 0

        # next_retry_at が未来なので現在時刻では取得されない
        pending = outbox.list_pending(now=now)
        assert len(pending) == 0

        # 未来時刻では取得される（retry対象）
        future = now + timedelta(minutes=2)
        pending = outbox.list_pending(now=future)
        assert len(pending) == 1
        assert pending[0].retry_count == 1
        assert "RuntimeError" in pending[0].last_error
