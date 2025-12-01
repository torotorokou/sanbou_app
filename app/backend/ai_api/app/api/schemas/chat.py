from pydantic import BaseModel
from typing import List

class ChatRequest(BaseModel):
    query: str
    tags: List[str] = []
    pdf: str = ""
