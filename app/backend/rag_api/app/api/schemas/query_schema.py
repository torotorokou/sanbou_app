from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str
    category: str
    tags: list[str] | None = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[str]
    pages: list[str]
