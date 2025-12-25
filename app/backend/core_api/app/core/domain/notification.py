"""
Notification Domain Models

外部依存ゼロ。通知の型・不変条件を定義。

Recipient Key 規約:
  - user:{id}     : 自社ユーザー（例: user:123）
  - email:{addr}  : メールアドレス（例: email:user@example.com）
  - aud:{site}:{code} : 顧客コード（例: aud:site:narita）

  将来的にLINE送信時は、RecipientResolverが user:123 → LINE user ID に解決する。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional
from uuid import UUID, uuid4

# 通知チャネル（将来拡張可能）
NotificationChannel = Literal["email", "line", "webhook", "push"]


class NotificationStatus(str, Enum):
    """通知ステータス"""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"


class FailureType(str, Enum):
    """
    送信失敗の種別

    - TEMPORARY: 一時的な失敗（リトライ可能）
      例: ネットワークエラー、タイムアウト、一時的なAPI制限
    - PERMANENT: 恒久的な失敗（リトライ不要）
      例: 無効なrecipient、通知許可なし、Resolver解決不可
    """

    TEMPORARY = "temporary"
    PERMANENT = "permanent"


@dataclass(frozen=True)
class RecipientRef:
    """
    通知送信先の参照

    自社システム内のキーで通知先を表現する。
    チャネル固有のID（LINE user ID等）は含めない。

    Examples:
        RecipientRef(kind="user", key="123")      -> "user:123"
        RecipientRef(kind="email", key="a@b.com") -> "email:a@b.com"
        RecipientRef(kind="aud", key="site:narita") -> "aud:site:narita"
    """

    kind: Literal["user", "email", "aud"]
    key: str

    def __post_init__(self):
        if not self.key.strip():
            raise ValueError("recipient key must not be empty")

    def as_string(self) -> str:
        """文字列表現（recipient_keyとして使用）"""
        return f"{self.kind}:{self.key}"

    @staticmethod
    def parse(recipient_key: str) -> Optional["RecipientRef"]:
        """
        recipient_key文字列から RecipientRef を生成

        Args:
            recipient_key: "user:123" 等の形式

        Returns:
            RecipientRef or None (パース失敗時)
        """
        parts = recipient_key.split(":", 1)
        if len(parts) != 2:
            return None
        kind, key = parts
        if kind not in ("user", "email", "aud"):
            return None
        return RecipientRef(kind=kind, key=key)  # type: ignore


@dataclass(frozen=True)
class NotificationPayload:
    """通知ペイロード（チャネル共通の最小構造）"""

    title: str
    body: str
    url: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)

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
    - dispatch で処理され、sent/failed/skipped に遷移
    - 失敗時は failure_type で TEMP/PERM を判定し、retry_count と next_retry_at で再試行制御
    """

    id: UUID
    channel: NotificationChannel
    status: NotificationStatus
    payload: NotificationPayload
    recipient_key: str  # "user:123", "email:a@b.com", "aud:site:narita" 形式
    created_at: datetime
    scheduled_at: datetime | None = None
    sent_at: datetime | None = None
    retry_count: int = 0
    next_retry_at: datetime | None = None
    last_error: str | None = None
    failure_type: FailureType | None = None  # TEMPORARY/PERMANENT

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
        scheduled_at: datetime | None = None,
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


@dataclass(frozen=True)
class NotificationPreference:
    """
    ユーザーの通知許可設定

    将来的にはDB永続化される想定。
    今回はInMemory実装で枠だけ用意。
    """

    user_key: str  # "user:123" 形式
    email_enabled: bool = True
    line_enabled: bool = False  # デフォルトは無効（LINE連携が必要）
    critical_only: bool = False  # 重要通知のみ（今回未使用）

    def __post_init__(self):
        if not self.user_key.strip():
            raise ValueError("user_key must not be empty")
        # user: プレフィックスの検証（任意）
        if not self.user_key.startswith("user:"):
            raise ValueError("user_key must start with 'user:'")
