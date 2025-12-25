from typing import List

from pydantic import BaseModel


class ChatRequest(BaseModel):
    query: str
    tags: List[str] = []
    pdf: str = ""
