"""
ジョブ管理ドメインモデル

目的:
- 非同期処理のジョブ状態を管理
- 失敗時に ProblemDetails を保持
"""

from typing import Optional, Literal, Any
from pydantic import BaseModel, Field

from .contract import ProblemDetails

JobStatusType = Literal['pending', 'running', 'completed', 'failed', 'cancelled']


class JobStatus(BaseModel):
    """
    ジョブステータスDTO
    
    フィールド:
    - id: ジョブID
    - status: ジョブの状態
    - progress: 進捗率 (0-100)
    - message: 状態メッセージ
    - result: 成功時の結果データ
    - error: 失敗時の ProblemDetails
    - createdAt: 作成日時
    - updatedAt: 更新日時
    """
    id: str
    status: JobStatusType
    progress: int = Field(default=0, ge=0, le=100)
    message: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[ProblemDetails] = None  # 失敗時の詳細エラー情報
    createdAt: str = Field(alias='createdAt')
    updatedAt: str = Field(alias='updatedAt')
    
    class Config:
        populate_by_name = True


class JobCreate(BaseModel):
    """
    ジョブ作成リクエスト
    """
    feature: str
    parameters: Optional[dict] = None


class JobUpdate(BaseModel):
    """
    ジョブ更新リクエスト
    """
    status: Optional[JobStatusType] = None
    progress: Optional[int] = Field(default=None, ge=0, le=100)
    message: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[ProblemDetails] = None
