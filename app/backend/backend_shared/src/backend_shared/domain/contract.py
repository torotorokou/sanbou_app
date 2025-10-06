"""
通知契約モデル（OpenAPI準拠）

目的:
- フロント/バック共通の通知スキーマをPydanticで定義
- contracts/notifications.openapi.yaml と完全一致
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field

Severity = Literal['success', 'info', 'warning', 'error']


class ProblemDetails(BaseModel):
    """
    RFC 7807 Problem Details 準拠のエラー情報
    
    OpenAPI契約:
    - status (必須): HTTPステータスコード
    - code (必須): アプリケーション固有のエラーコード
    - userMessage (必須): ユーザー向けメッセージ
    - title (任意): エラータイトル
    - traceId (任意): トレースID
    """
    status: int
    code: str
    userMessage: str = Field(alias='userMessage')
    title: Optional[str] = None
    traceId: Optional[str] = Field(default=None, alias='traceId')

    class Config:
        populate_by_name = True  # Pydantic v2: allow both snake_case and camelCase


class NotificationEvent(BaseModel):
    """
    通知イベントモデル
    
    OpenAPI契約:
    - id (必須): UUID形式の通知ID
    - severity (必須): success/info/warning/error
    - title (必須): 通知タイトル
    - message (任意): 詳細メッセージ
    - duration (任意): 表示時間(ms) / null=自動削除なし
    - feature (任意): 機能名
    - resultUrl (任意): 結果URL
    - jobId (任意): ジョブID
    - traceId (任意): トレースID
    - createdAt (必須): 作成日時(ISO8601)
    """
    id: str
    severity: Severity
    title: str
    message: Optional[str] = None
    duration: Optional[int] = None
    feature: Optional[str] = None
    resultUrl: Optional[str] = Field(default=None, alias='resultUrl')
    jobId: Optional[str] = Field(default=None, alias='jobId')
    traceId: Optional[str] = Field(default=None, alias='traceId')
    createdAt: str = Field(alias='createdAt')

    class Config:
        populate_by_name = True  # Pydantic v2: allow both snake_case and camelCase
