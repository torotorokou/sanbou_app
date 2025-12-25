"""Block Unit Price API schemas."""

from __future__ import annotations

from typing import List, Union

from pydantic import BaseModel, Field, validator


class TransportCandidateRowDTO(BaseModel):
    """運搬候補行レスポンススキーマ"""

    entry_id: str
    vendor_code: Union[int, str]
    vendor_name: str
    item_name: str
    detail: str | None = None
    options: List[str] = Field(default_factory=list)
    initial_index: int = 0

    @validator("options", pre=True)
    def ensure_options(cls, value: List[str]) -> List[str]:  # type: ignore[override]
        if value is None:
            return []
        return list(value)


class TransportCandidateResponseDTO(BaseModel):
    """ブロック単価表インタラクティブ初期レスポンススキーマ"""

    session_id: str
    rows: List[TransportCandidateRowDTO] = Field(default_factory=list)
