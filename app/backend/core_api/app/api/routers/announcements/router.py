"""
Announcements API Router
お知らせ（アナウンスメント）の取得・状態更新API
"""

from datetime import datetime
from typing import List, Optional

from app.core.domain.announcement import (
    Announcement,
    AnnouncementSeverity,
    AnnouncementWithState,
    Audience,
)
from app.core.domain.auth.entities import AuthUser
from app.deps import get_current_user, get_db
from app.infra.adapters.announcement import AnnouncementRepositoryImpl
from backend_shared.application.logging import create_log_context, get_module_logger
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

logger = get_module_logger(__name__)

router = APIRouter(prefix="/announcements", tags=["announcements"])


# ========================================
# Response Models
# ========================================


class AnnouncementListItem(BaseModel):
    """お知らせ一覧用レスポンス"""

    id: int
    title: str
    severity: AnnouncementSeverity
    tags: List[str]
    publish_from: datetime
    publish_to: Optional[datetime]
    audience: Audience
    read_at: Optional[datetime]
    ack_at: Optional[datetime]
    created_at: datetime


class AnnouncementDetail(BaseModel):
    """お知らせ詳細レスポンス"""

    id: int
    title: str
    body_md: str
    severity: AnnouncementSeverity
    tags: List[str]
    publish_from: datetime
    publish_to: Optional[datetime]
    audience: Audience
    attachments: list
    notification_plan: Optional[dict]
    read_at: Optional[datetime]
    ack_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class AnnouncementListResponse(BaseModel):
    """お知らせ一覧APIレスポンス"""

    announcements: List[AnnouncementListItem]
    total: int
    unread_count: int


class UnreadCountResponse(BaseModel):
    """未読数レスポンス"""

    unread_count: int


class MarkReadRequest(BaseModel):
    """既読マークリクエスト"""

    announcement_id: int = Field(..., description="お知らせID")


class MarkReadResponse(BaseModel):
    """既読マークレスポンス"""

    success: bool
    announcement_id: int
    read_at: datetime


class MarkAcknowledgedResponse(BaseModel):
    """確認済みマークレスポンス"""

    success: bool
    announcement_id: int
    ack_at: datetime


# ========================================
# Endpoints
# ========================================


@router.get("", response_model=AnnouncementListResponse)
async def list_announcements(
    audience: Optional[str] = Query(
        None, description="対象フィルタ (all, internal, site:narita, site:shinkiba)"
    ),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """
    アクティブなお知らせ一覧を取得

    - 公開中かつ未削除のお知らせを返す
    - ユーザーごとの既読・確認状態を含む
    - publish_from DESC順（新しいものから）
    """
    user_id = current_user.email

    logger.info(
        "Listing announcements",
        extra=create_log_context(
            operation="list_announcements",
            user_id=user_id,
            audience=audience,
        ),
    )

    repo = AnnouncementRepositoryImpl(db)

    announcements_with_state = repo.list_active(user_id=user_id, audience=audience)
    unread_count = repo.get_unread_count(user_id=user_id, audience=audience)

    items = []
    for aws in announcements_with_state:
        ann = aws.announcement
        items.append(
            AnnouncementListItem(
                id=ann.id,
                title=ann.title,
                severity=ann.severity,
                tags=ann.tags,
                publish_from=ann.publish_from,
                publish_to=ann.publish_to,
                audience=ann.audience,
                read_at=aws.read_at,
                ack_at=aws.ack_at,
                created_at=ann.created_at,
            )
        )

    return AnnouncementListResponse(
        announcements=items,
        total=len(items),
        unread_count=unread_count,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    audience: Optional[str] = Query(None, description="対象フィルタ"),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """
    未読お知らせ数を取得

    サイドバーのバッジ表示用
    """
    user_id = current_user.email

    repo = AnnouncementRepositoryImpl(db)
    count = repo.get_unread_count(user_id=user_id, audience=audience)

    return UnreadCountResponse(unread_count=count)


@router.get("/{announcement_id}", response_model=AnnouncementDetail)
async def get_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """
    お知らせ詳細を取得

    - 指定IDのお知らせを返す
    - 自動的に既読にはしない（別途POSTで既読化）
    """
    user_id = current_user.email

    logger.info(
        "Getting announcement detail",
        extra=create_log_context(
            operation="get_announcement",
            user_id=user_id,
            announcement_id=announcement_id,
        ),
    )

    repo = AnnouncementRepositoryImpl(db)
    result = repo.get_by_id(announcement_id=announcement_id, user_id=user_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Announcement not found")

    ann = result.announcement
    return AnnouncementDetail(
        id=ann.id,
        title=ann.title,
        body_md=ann.body_md,
        severity=ann.severity,
        tags=ann.tags,
        publish_from=ann.publish_from,
        publish_to=ann.publish_to,
        audience=ann.audience,
        attachments=[att.model_dump() for att in ann.attachments],
        notification_plan=(
            ann.notification_plan.model_dump() if ann.notification_plan else None
        ),
        read_at=result.read_at,
        ack_at=result.ack_at,
        created_at=ann.created_at,
        updated_at=ann.updated_at,
    )


@router.post("/{announcement_id}/read", response_model=MarkReadResponse)
async def mark_as_read(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """
    お知らせを既読にする

    - 詳細画面表示時にフロントエンドから呼び出し
    - すでに既読の場合は何もしない（冪等）
    """
    user_id = current_user.email

    logger.info(
        "Marking announcement as read",
        extra=create_log_context(
            operation="mark_as_read",
            user_id=user_id,
            announcement_id=announcement_id,
        ),
    )

    repo = AnnouncementRepositoryImpl(db)

    # Check announcement exists
    announcement = repo.get_by_id(announcement_id=announcement_id, user_id=user_id)
    if announcement is None:
        raise HTTPException(status_code=404, detail="Announcement not found")

    state = repo.mark_read(announcement_id=announcement_id, user_id=user_id)

    return MarkReadResponse(
        success=True,
        announcement_id=announcement_id,
        read_at=state.read_at,
    )


@router.post("/{announcement_id}/acknowledge", response_model=MarkAcknowledgedResponse)
async def mark_as_acknowledged(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """
    お知らせを確認済みにする（critical用）

    - critical重要度のお知らせ用
    - 確認ボタン押下時にフロントエンドから呼び出し
    - すでに確認済みの場合は何もしない（冪等）
    """
    user_id = current_user.email

    logger.info(
        "Marking announcement as acknowledged",
        extra=create_log_context(
            operation="mark_as_acknowledged",
            user_id=user_id,
            announcement_id=announcement_id,
        ),
    )

    repo = AnnouncementRepositoryImpl(db)

    # Check announcement exists
    announcement = repo.get_by_id(announcement_id=announcement_id, user_id=user_id)
    if announcement is None:
        raise HTTPException(status_code=404, detail="Announcement not found")

    state = repo.mark_acknowledged(announcement_id=announcement_id, user_id=user_id)

    return MarkAcknowledgedResponse(
        success=True,
        announcement_id=announcement_id,
        ack_at=state.ack_at,
    )
