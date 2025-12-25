# -*- coding: utf-8 -*-
"""
Announcement repository implementation with PostgreSQL.
お知らせデータ（お知らせ本体・ユーザー状態）の取得・更新
"""
from datetime import datetime, timezone
from typing import List, Optional

from app.core.domain.announcement import (
    Announcement,
    AnnouncementUserState,
    AnnouncementWithState,
    Attachment,
    NotificationPlan,
)
from app.core.ports.announcement_repository_port import AnnouncementRepositoryPort
from app.infra.db.orm_models import AnnouncementORM, AnnouncementUserStateORM
from backend_shared.application.logging import get_module_logger
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

logger = get_module_logger(__name__)


def _orm_to_domain(orm_obj: AnnouncementORM) -> Announcement:
    """ORMモデルをドメインモデルに変換"""
    attachments = []
    if orm_obj.attachments:
        for att in orm_obj.attachments:
            attachments.append(Attachment(**att))

    notification_plan = None
    if orm_obj.notification_plan:
        notification_plan = NotificationPlan(**orm_obj.notification_plan)

    return Announcement(
        id=orm_obj.id,
        title=orm_obj.title,
        body_md=orm_obj.body_md,
        severity=orm_obj.severity,
        tags=orm_obj.tags or [],
        publish_from=orm_obj.publish_from,
        publish_to=orm_obj.publish_to,
        audience=orm_obj.audience,
        attachments=attachments,
        notification_plan=notification_plan,
        created_at=orm_obj.created_at,
        updated_at=orm_obj.updated_at,
    )


def _state_orm_to_domain(orm_obj: AnnouncementUserStateORM) -> AnnouncementUserState:
    """ユーザー状態ORMをドメインモデルに変換"""
    return AnnouncementUserState(
        id=orm_obj.id,
        user_id=orm_obj.user_id,
        announcement_id=orm_obj.announcement_id,
        read_at=orm_obj.read_at,
        ack_at=orm_obj.ack_at,
    )


class AnnouncementRepositoryImpl(AnnouncementRepositoryPort):
    """
    PostgreSQL implementation of AnnouncementRepository.
    """

    def __init__(self, db: Session):
        self.db = db

    def list_active(
        self,
        user_id: str,
        audience: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> List[AnnouncementWithState]:
        """アクティブなお知らせ一覧を取得（公開中かつ未削除）"""
        if now is None:
            now = datetime.now(timezone.utc)

        try:
            # Base query: active (not deleted) and published
            conditions = [
                AnnouncementORM.deleted_at == None,
                AnnouncementORM.publish_from <= now,
            ]

            # Optional audience filter
            if audience and audience != "all":
                # Match exact audience or 'all'
                conditions.append(AnnouncementORM.audience.in_([audience, "all"]))

            # Subquery for user state
            user_state_subq = (
                select(
                    AnnouncementUserStateORM.announcement_id,
                    AnnouncementUserStateORM.read_at,
                    AnnouncementUserStateORM.ack_at,
                )
                .where(AnnouncementUserStateORM.user_id == user_id)
                .subquery()
            )

            # Main query with left join
            stmt = (
                select(
                    AnnouncementORM,
                    user_state_subq.c.read_at,
                    user_state_subq.c.ack_at,
                )
                .outerjoin(
                    user_state_subq,
                    AnnouncementORM.id == user_state_subq.c.announcement_id,
                )
                .where(and_(*conditions))
                .where(
                    # Not expired: publish_to is NULL or > now
                    (AnnouncementORM.publish_to == None)
                    | (AnnouncementORM.publish_to > now)
                )
                .order_by(AnnouncementORM.publish_from.desc())
            )

            results = self.db.execute(stmt).all()

            announcements_with_state = []
            for row in results:
                announcement_orm = row[0]
                read_at = row[1]
                ack_at = row[2]

                announcement = _orm_to_domain(announcement_orm)
                announcements_with_state.append(
                    AnnouncementWithState(
                        announcement=announcement,
                        read_at=read_at,
                        ack_at=ack_at,
                    )
                )

            return announcements_with_state

        except Exception as e:
            logger.error(f"Failed to list active announcements: {e}", exc_info=True)
            raise

    def get_by_id(
        self,
        announcement_id: int,
        user_id: str,
    ) -> Optional[AnnouncementWithState]:
        """指定IDのお知らせを取得"""
        try:
            # Subquery for user state
            user_state_subq = (
                select(
                    AnnouncementUserStateORM.announcement_id,
                    AnnouncementUserStateORM.read_at,
                    AnnouncementUserStateORM.ack_at,
                )
                .where(AnnouncementUserStateORM.user_id == user_id)
                .subquery()
            )

            stmt = (
                select(
                    AnnouncementORM,
                    user_state_subq.c.read_at,
                    user_state_subq.c.ack_at,
                )
                .outerjoin(
                    user_state_subq,
                    AnnouncementORM.id == user_state_subq.c.announcement_id,
                )
                .where(
                    and_(
                        AnnouncementORM.id == announcement_id,
                        AnnouncementORM.deleted_at == None,
                    )
                )
            )

            row = self.db.execute(stmt).first()

            if row is None:
                return None

            announcement_orm = row[0]
            read_at = row[1]
            ack_at = row[2]

            announcement = _orm_to_domain(announcement_orm)
            return AnnouncementWithState(
                announcement=announcement,
                read_at=read_at,
                ack_at=ack_at,
            )

        except Exception as e:
            logger.error(f"Failed to get announcement by id: {e}", exc_info=True)
            raise

    def mark_read(
        self,
        announcement_id: int,
        user_id: str,
    ) -> AnnouncementUserState:
        """お知らせを既読にする"""
        try:
            now = datetime.now(timezone.utc)

            # Check if state exists
            existing = self.db.execute(
                select(AnnouncementUserStateORM).where(
                    and_(
                        AnnouncementUserStateORM.user_id == user_id,
                        AnnouncementUserStateORM.announcement_id == announcement_id,
                    )
                )
            ).scalar_one_or_none()

            if existing:
                # Already exists, update read_at if not set
                if existing.read_at is None:
                    existing.read_at = now
                    existing.updated_at = now
                    self.db.flush()
                return _state_orm_to_domain(existing)
            else:
                # Create new state
                new_state = AnnouncementUserStateORM(
                    user_id=user_id,
                    announcement_id=announcement_id,
                    read_at=now,
                    created_at=now,
                    updated_at=now,
                )
                self.db.add(new_state)
                self.db.flush()
                return _state_orm_to_domain(new_state)

        except Exception as e:
            logger.error(f"Failed to mark announcement as read: {e}", exc_info=True)
            raise

    def mark_acknowledged(
        self,
        announcement_id: int,
        user_id: str,
    ) -> AnnouncementUserState:
        """お知らせを確認済みにする（critical用）"""
        try:
            now = datetime.now(timezone.utc)

            # Check if state exists
            existing = self.db.execute(
                select(AnnouncementUserStateORM).where(
                    and_(
                        AnnouncementUserStateORM.user_id == user_id,
                        AnnouncementUserStateORM.announcement_id == announcement_id,
                    )
                )
            ).scalar_one_or_none()

            if existing:
                # Update ack_at and read_at (acknowledged implies read)
                if existing.ack_at is None:
                    existing.ack_at = now
                if existing.read_at is None:
                    existing.read_at = now
                existing.updated_at = now
                self.db.flush()
                return _state_orm_to_domain(existing)
            else:
                # Create new state (both read and ack)
                new_state = AnnouncementUserStateORM(
                    user_id=user_id,
                    announcement_id=announcement_id,
                    read_at=now,
                    ack_at=now,
                    created_at=now,
                    updated_at=now,
                )
                self.db.add(new_state)
                self.db.flush()
                return _state_orm_to_domain(new_state)

        except Exception as e:
            logger.error(
                f"Failed to mark announcement as acknowledged: {e}", exc_info=True
            )
            raise

    def get_unread_count(
        self,
        user_id: str,
        audience: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> int:
        """未読お知らせ数を取得"""
        if now is None:
            now = datetime.now(timezone.utc)

        try:
            # Subquery for user state
            user_state_subq = (
                select(AnnouncementUserStateORM.announcement_id)
                .where(
                    and_(
                        AnnouncementUserStateORM.user_id == user_id,
                        AnnouncementUserStateORM.read_at != None,
                    )
                )
                .subquery()
            )

            # Base conditions: active and not read
            conditions = [
                AnnouncementORM.deleted_at == None,
                AnnouncementORM.publish_from <= now,
                (AnnouncementORM.publish_to == None)
                | (AnnouncementORM.publish_to > now),
                AnnouncementORM.id.notin_(select(user_state_subq.c.announcement_id)),
            ]

            # Optional audience filter
            if audience and audience != "all":
                conditions.append(AnnouncementORM.audience.in_([audience, "all"]))

            stmt = (
                select(func.count())
                .select_from(AnnouncementORM)
                .where(and_(*conditions))
            )

            result = self.db.execute(stmt).scalar()
            return result or 0

        except Exception as e:
            logger.error(f"Failed to get unread count: {e}", exc_info=True)
            raise
