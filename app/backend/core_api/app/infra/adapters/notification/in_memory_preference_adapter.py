"""
InMemory Notification Preference Adapter

開発・テスト用のインメモリ実装。
将来的にはDBから取得する。
"""

from typing import Dict, Optional

from app.core.domain.notification import NotificationPreference
from app.core.ports.notification_port import NotificationPreferencePort
from backend_shared.application.logging import get_module_logger

logger = get_module_logger(__name__)


class InMemoryNotificationPreferenceAdapter(NotificationPreferencePort):
    """
    InMemory Preference 実装

    固定マップでユーザーの通知許可設定を管理。
    """

    def __init__(self):
        # デフォルト設定（開発・テスト用）
        self._preferences: Dict[str, NotificationPreference] = {
            "user:1": NotificationPreference(
                user_key="user:1",
                email_enabled=True,
                line_enabled=True,  # LINE許可
            ),
            "user:2": NotificationPreference(
                user_key="user:2",
                email_enabled=True,
                line_enabled=False,  # LINE無効
            ),
            "user:3": NotificationPreference(
                user_key="user:3",
                email_enabled=False,  # Email無効
                line_enabled=True,
            ),
        }
        logger.info("[Preference] InMemory adapter initialized")

    def get_for_recipient(self, recipient_key: str) -> Optional[NotificationPreference]:
        """
        recipient_key に対応する通知許可設定を取得

        Args:
            recipient_key: "user:123" 形式

        Returns:
            NotificationPreference or None (設定なし = 全て許可)
        """
        pref = self._preferences.get(recipient_key)
        if pref:
            logger.debug(
                f"[Preference] Found preference for {recipient_key}",
                extra={
                    "recipient_key": recipient_key,
                    "email_enabled": pref.email_enabled,
                    "line_enabled": pref.line_enabled,
                },
            )
        else:
            logger.debug(
                f"[Preference] No preference for {recipient_key} (default: all enabled)"
            )
        return pref
