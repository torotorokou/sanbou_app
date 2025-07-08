from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import requests
import os
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = FastAPI()

class ChatRequest(BaseModel):
    query: str
    tags: List[str] = []
    pdf: str = ""

@app.post("/api/chat")
def chat(req: ChatRequest):
    prompt = f"""
以下はPDFに関連する質問です。

質問: {req.query}
関連タグ: {', '.join(req.tags)}
関連PDF: {req.pdf or '指定なし'}

質問に対して分かりやすく答えてください。
    """

    try:
        # ✅ 最新版：無料対応の Flash モデル + generateContent 使用
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={
                "contents": [
                    {
                        "parts": [{"text": prompt}]
                    }
                ]
            }
        )
        response.raise_for_status()
        data = response.json()

        # ✅ Flash モデルの返答の取り出し
        answer = data["candidates"][0]["content"]["parts"][0]["text"]

        return {
            "answer": answer,
            "sources": [
                {
                    "pdf": req.pdf or "doc1.pdf",
                    "section_title": "Gemini応答より",
                    "highlight": req.query
                }
            ]
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "answer": f"Gemini APIとの通信に失敗しました。\nエラー: {str(e)}",
            "sources": []
        }
