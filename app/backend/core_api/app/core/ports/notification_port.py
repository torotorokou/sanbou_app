"""
Notification Ports - 抽象インターフェイス

UseCase が依存する抽象。具体実装は infra/adapters に置く。
"""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.core.domain.notification import (
    FailureType,
    NotificationChannel,
    NotificationOutboxItem,
    NotificationPayload,
    NotificationPreference,
)


class NotificationOutboxPort(ABC):
    """
    通知 Outbox リポジトリの抽象

    - enqueue: 通知要求を登録
    - list_pending: 送信対象の pending アイテムを取得
    - mark_sent: 送信成功をマーク
    - mark_failed: 送信失敗をマーク（リトライ情報更新）
    - mark_skipped: 送信スキップをマーク（PERMANENT失敗、通知無効等）
    """

    @abstractmethod
    def enqueue(self, items: list[NotificationOutboxItem]) -> None:
        """通知アイテムを Outbox に登録"""
        pass

    @abstractmethod
    def list_pending(
        self, now: datetime, limit: int = 100
    ) -> list[NotificationOutboxItem]:
        """
        送信対象の pending アイテムを取得

        条件:
        - status='pending'
        - (scheduled_at is None OR scheduled_at <= now)
        - (next_retry_at is None OR next_retry_at <= now)
        """
        pass

    @abstractmethod
    def mark_sent(self, id: UUID, sent_at: datetime) -> None:
        """通知送信成功をマーク"""
        pass

    @abstractmethod
    def mark_failed(
        self, id: UUID, error: str, failure_type: FailureType, now: datetime
    ) -> None:
        """
        通知送信失敗をマーク

        - TEMPORARY: status を pending に戻し、retry_count をインクリメント、next_retry_at を設定
        - PERMANENT: status を failed に更新（リトライなし）
        - last_error に失敗理由を保存
        - failure_type を保存
        """
        pass

    @abstractmethod
    def mark_skipped(self, id: UUID, reason: str, now: datetime) -> None:
        """
        通知送信スキップをマーク

        - status を skipped に更新
        - last_error に理由を保存
        - リトライ対象外

        使用例:
        - ユーザーが通知を無効にしている
        - recipient解決不可（LINE未連携等）
        """
        pass


class NotificationSenderPort(ABC):
    """
    通知送信の抽象（チャネル共通）

    - send: 指定チャネルで通知を送信

    将来的にチャネル別ポートに分割可能
    （EmailSenderPort, LineSenderPort 等）
    """

    @abstractmethod
    def send(
        self,
        channel: NotificationChannel,
        payload: NotificationPayload,
        recipient_key: str,
    ) -> None:
        """
        通知を送信

        実装側で例外を投げることで失敗を通知。
        UseCase 側で catch して mark_failed を呼ぶ。
        """
        pass


class NotificationPreferencePort(ABC):
    """
    通知許可設定の抽象

    ユーザーがどの通知チャネルを許可しているかを管理。
    将来的にDB永続化される想定（今回はInMemory）。
    """

    @abstractmethod
    def get_for_recipient(self, recipient_key: str) -> NotificationPreference | None:
        """
        recipient_key に対応する通知許可設定を取得

        Args:
            recipient_key: "user:123" 形式の受信者キー

        Returns:
            NotificationPreference or None (設定なし = 全て許可と解釈可)
        """
        pass


class RecipientResolverPort(ABC):
    """
    recipient_key をチャネル固有のIDに解決する抽象

    例:
    - user:123, channel=line  → LINE user ID "Uxxxxxxxx"
    - user:123, channel=email → ユーザーのメールアドレス
    - email:a@b.com, channel=email → "a@b.com" (そのまま)

    将来的にDBやUser管理システムと連携する想定（今回はDummy）。
    """

    @abstractmethod
    def resolve(self, recipient_key: str, channel: NotificationChannel) -> str | None:
        """
        recipient_key をチャネル固有のIDに解決

        Args:
            recipient_key: "user:123", "email:a@b.com" 等
            channel: 送信チャネル

        Returns:
            チャネル固有のID or None (解決不可)

        Examples:
            resolve("user:123", "line")  -> "Uxxxxxxxx" or None (未連携)
            resolve("user:123", "email") -> "user@example.com" or None
            resolve("email:a@b.com", "email") -> "a@b.com"
        """
        pass
