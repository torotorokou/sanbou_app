"""
Announcement domain entities.
お知らせ（アナウンスメント）のドメインエンティティ
"""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


AnnouncementSeverity = Literal["info", "warn", "critical"]
Audience = Literal["all", "internal", "site:narita", "site:shinkiba"]


class Attachment(BaseModel):
    """添付ファイル情報"""
    label: str = Field(..., description="表示ラベル")
    url: str = Field(..., description="ファイルURL")


class NotificationPlan(BaseModel):
    """通知設定"""
    email: bool = Field(False, description="メール通知")
    in_app: bool = Field(True, description="アプリ内通知")


class Announcement(BaseModel):
    """
    お知らせデータ (app.announcements)
    
    Fields:
        id: お知らせID (PK)
        title: タイトル
        body_md: 本文（Markdown形式）
        severity: 重要度 ('info' | 'warn' | 'critical')
        tags: タグ配列
        publish_from: 公開開始日時
        publish_to: 公開終了日時（NULL=無期限）
        audience: 対象 ('all' | 'internal' | 'site:narita' | 'site:shinkiba')
        attachments: 添付ファイル配列
        notification_plan: 通知設定
        created_at: 作成日時
        updated_at: 更新日時
    """
    id: int = Field(..., description="お知らせID")
    title: str = Field(..., description="タイトル")
    body_md: str = Field(..., description="本文（Markdown形式）")
    severity: AnnouncementSeverity = Field("info", description="重要度")
    tags: List[str] = Field(default_factory=list, description="タグ配列")
    publish_from: datetime = Field(..., description="公開開始日時")
    publish_to: Optional[datetime] = Field(None, description="公開終了日時")
    audience: Audience = Field("all", description="対象")
    attachments: List[Attachment] = Field(default_factory=list, description="添付ファイル配列")
    notification_plan: Optional[NotificationPlan] = Field(None, description="通知設定")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")

    class Config:
        from_attributes = True


class AnnouncementUserState(BaseModel):
    """
    ユーザーごとのお知らせ既読・確認状態 (app.announcement_user_states)
    
    Fields:
        id: 状態ID (PK)
        user_id: ユーザー識別子
        announcement_id: お知らせID (FK)
        read_at: 既読日時（NULL=未読）
        ack_at: 確認日時（NULL=未確認、criticalお知らせ用）
    """
    id: int = Field(..., description="状態ID")
    user_id: str = Field(..., description="ユーザー識別子")
    announcement_id: int = Field(..., description="お知らせID")
    read_at: Optional[datetime] = Field(None, description="既読日時")
    ack_at: Optional[datetime] = Field(None, description="確認日時")

    class Config:
        from_attributes = True


class AnnouncementWithState(BaseModel):
    """
    ユーザー状態を含むお知らせデータ
    APIレスポンス用
    """
    announcement: Announcement
    read_at: Optional[datetime] = None
    ack_at: Optional[datetime] = None

    class Config:
        from_attributes = True
