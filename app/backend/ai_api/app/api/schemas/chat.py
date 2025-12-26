from pydantic import BaseModel


class ChatRequest(BaseModel):
    query: str
    tags: list[str] = []
    pdf: str = ""
