import os, sys
from dotenv import load_dotenv
from pathlib import Path
from app.paths import CONFIG_ENV

# config/.env を読み込み
load_dotenv(dotenv_path=CONFIG_ENV)

# PYTHONPATH を取得して sys.path に追加（任意で .env に設定）
py_path = os.getenv("PYTHONPATH")
if py_path:
    full_path = (Path(__file__).resolve() / py_path).resolve()
    if str(full_path) not in sys.path:
        sys.path.append(str(full_path))

# --- FastAPI 本体
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import query  # ← query.py に router を定義

# FastAPIアプリケーションのインスタンスを作成
app = FastAPI(
    title="RAG_API",
    version="1.0.0",
    root_path="/rag_api",  # API全体のベースパスを指定
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# --- CORS設定（Reactなどからの呼び出し用）
origins = [
    "http://localhost:3000",  # フロントエンド開発時のURL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- APIルーター登録
app.include_router(query.router, prefix="/api")


# --- 動作確認用のルート
@app.get("/")
async def root():
    return {"message": "Welcome to the Sanbo Navi API"}
