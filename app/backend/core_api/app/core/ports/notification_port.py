"""
Notification Ports - 抽象インターフェイス

UseCase が依存する抽象。具体実装は infra/adapters に置く。
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List
from uuid import UUID

from app.core.domain.notification import (
    NotificationChannel,
    NotificationOutboxItem,
    NotificationPayload,
)


class NotificationOutboxPort(ABC):
    """
    通知 Outbox リポジトリの抽象
    
    - enqueue: 通知要求を登録
    - list_pending: 送信対象の pending アイテムを取得
    - mark_sent: 送信成功をマーク
    - mark_failed: 送信失敗をマーク（リトライ情報更新）
    """

    @abstractmethod
    def enqueue(self, items: List[NotificationOutboxItem]) -> None:
        """通知アイテムを Outbox に登録"""
        pass

    @abstractmethod
    def list_pending(self, now: datetime, limit: int = 100) -> List[NotificationOutboxItem]:
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
    def mark_failed(self, id: UUID, error: str, now: datetime) -> None:
        """
        通知送信失敗をマーク
        
        - status を failed に更新
        - retry_count をインクリメント
        - next_retry_at を簡易バックオフで設定
        - last_error に失敗理由を保存
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
