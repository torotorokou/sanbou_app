from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import requests
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# .envからAPIキーを読み込む
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# FastAPIインスタンス作成
app = FastAPI()

# ==========================
# 🔹 CORS 許可設定（React からのアクセスを許可）
# ==========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 必要に応じて ["http://localhost:5173"] などに限定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================
# 🔹 チャットリクエストモデル
# ==========================
class ChatRequest(BaseModel):
    query: str
    tags: List[str] = []
    pdf: str = ""


# ==========================
# 🔸 /api/ai/chat : メイン質問応答
# ==========================
@app.post("/api/ai/chat")
def chat(req: ChatRequest):
    prompt = f"""
以下はPDFに関連する質問です。

質問: {req.query}
関連タグ: {", ".join(req.tags)}
関連PDF: {req.pdf or "指定なし"}

質問に対してわかりやすく丁寧に答えてください。
"""

    try:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
            f"?key={GEMINI_API_KEY}"
        )

        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]},
        )
        response.raise_for_status()
        data = response.json()
        answer = data["candidates"][0]["content"]["parts"][0]["text"]

        return {
            "answer": answer,
            "sources": [
                {
                    "pdf": req.pdf or "doc1.pdf",
                    "section_title": "Gemini応答より",
                    "highlight": req.query,
                }
            ],
        }

    except Exception as e:
        import traceback

        traceback.print_exc()
        return {
            "answer": f"Gemini APIとの通信に失敗しました。\nエラー: {str(e)}",
            "sources": [],
        }


# ==========================
# 🔸 /api/ai/intro : 初回説明文取得
# ==========================
@app.get("/api/ai/intro")
def get_intro():
    prompt = """
    あなたは、産業廃棄物に関する業務知識をナビゲートする参謀くんです。
    このアプリの初回説明として、以下の点を盛り込んで、自然な文章と改行で短く説明してください。

    - 自分は、産業廃棄物のプロAIである
    - 業務知識をサポートできる
    - ユーザーにカテゴリを選択してもらう導線を促す
    - フレンドリーかつ丁寧なトーン
    - こんにちは！など最初の挨拶は飛ばす。
    """

    try:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
            f"?key={GEMINI_API_KEY}"
        )

        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]},
        )
        response.raise_for_status()
        data = response.json()
        message = data["candidates"][0]["content"]["parts"][0]["text"]

        return {"text": message}

    except Exception as e:
        import traceback

        traceback.print_exc()
        return {"text": f"Gemini APIとの通信に失敗しました。エラー: {str(e)}"}


# ==========================
# 🔹 /api/ai/ping : 疎通確認用
# ==========================
@app.get("/api/ai/ping")
def ping():
    return {"message": "pong from ai_api"}
