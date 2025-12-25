"""
Dummy Recipient Resolver Adapter

開発・テスト用のダミー実装。
将来的にはUser管理システムやDB連携で実装する。
"""
from typing import Optional

from backend_shared.application.logging import get_module_logger

from app.core.domain.notification import NotificationChannel
from app.core.ports.notification_port import RecipientResolverPort

logger = get_module_logger(__name__)


class DummyRecipientResolverAdapter(RecipientResolverPort):
    """
    Dummy Resolver 実装
    
    - email: recipient_keyから抽出またはそのまま
    - line: 常にNone (未連携扱い)
    - 他: そのまま返す
    """

    def resolve(self, recipient_key: str, channel: NotificationChannel) -> Optional[str]:
        """
        recipient_key をチャネル固有のIDに解決
        
        今回はダミーなので:
        - email:xxx@example.com → xxx@example.com
        - user:xxx で channel=email → None (メールアドレス未登録)
        - user:xxx で channel=line → None (LINE未連携)
        """
        logger.debug(
            f"[Resolver] Resolving {recipient_key} for channel={channel}"
        )

        if channel == "email":
            # email: で始まる場合はメールアドレスを抽出
            if recipient_key.startswith("email:"):
                email = recipient_key.split(":", 1)[1]
                logger.debug(f"[Resolver] Resolved to email: {email}")
                return email
            # user: の場合は未登録扱い（実環境ではDBから取得）
            logger.debug(f"[Resolver] Email not found for {recipient_key}")
            return None

        elif channel == "line":
            # LINE はダミーなので常に None（未連携扱い）
            logger.debug(f"[Resolver] LINE not linked for {recipient_key}")
            return None

        else:
            # その他のチャネルはそのまま返す
            logger.debug(f"[Resolver] Pass-through for {channel}")
            return recipient_key
