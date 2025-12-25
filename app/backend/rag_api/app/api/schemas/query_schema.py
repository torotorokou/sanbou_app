from typing import List, Optional

from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str
    category: str
    tags: Optional[List[str]] = None


class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    pages: List[str]
