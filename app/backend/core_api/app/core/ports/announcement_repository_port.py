"""
Announcement repository port (abstract interface).
お知らせデータの取得・更新のポート定義
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from app.core.domain.announcement import (
    Announcement,
    AnnouncementUserState,
    AnnouncementWithState,
)


class AnnouncementRepositoryPort(ABC):
    """
    Announcement data repository interface.
    お知らせデータ（お知らせ本体・ユーザー状態）の取得・更新を抽象化
    """

    # ========================================
    # Announcement (お知らせ本体) Operations
    # ========================================

    @abstractmethod
    def list_active(
        self,
        user_id: str,
        audience: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> List[AnnouncementWithState]:
        """
        アクティブなお知らせ一覧を取得（公開中かつ未削除）

        Args:
            user_id: ユーザー識別子（既読状態取得用）
            audience: 対象フィルタ（オプション）
            now: 現在日時（テスト用、デフォルトはUTC now）

        Returns:
            お知らせとユーザー状態のリスト（publish_from DESC順）
        """
        pass

    @abstractmethod
    def get_by_id(
        self,
        announcement_id: int,
        user_id: str,
    ) -> Optional[AnnouncementWithState]:
        """
        指定IDのお知らせを取得

        Args:
            announcement_id: お知らせID
            user_id: ユーザー識別子（既読状態取得用）

        Returns:
            お知らせとユーザー状態（存在しない場合はNone）
        """
        pass

    # ========================================
    # User State (ユーザー状態) Operations
    # ========================================

    @abstractmethod
    def mark_read(
        self,
        announcement_id: int,
        user_id: str,
    ) -> AnnouncementUserState:
        """
        お知らせを既読にする

        Args:
            announcement_id: お知らせID
            user_id: ユーザー識別子

        Returns:
            更新されたユーザー状態
        """
        pass

    @abstractmethod
    def mark_acknowledged(
        self,
        announcement_id: int,
        user_id: str,
    ) -> AnnouncementUserState:
        """
        お知らせを確認済みにする（critical用）

        Args:
            announcement_id: お知らせID
            user_id: ユーザー識別子

        Returns:
            更新されたユーザー状態
        """
        pass

    @abstractmethod
    def get_unread_count(
        self,
        user_id: str,
        audience: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> int:
        """
        未読お知らせ数を取得

        Args:
            user_id: ユーザー識別子
            audience: 対象フィルタ（オプション）
            now: 現在日時（テスト用）

        Returns:
            未読お知らせ数
        """
        pass
