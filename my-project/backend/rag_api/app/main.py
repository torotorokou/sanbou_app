# --- バリデーションエラー時のカスタムレスポンス ---

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from app.paths import CONFIG_ENV
from app.api.endpoints import query  # ← query.py に router を定義

# --- .env読込
load_dotenv(dotenv_path=CONFIG_ENV)

# --- PYTHONPATH追加（任意）
py_path = os.getenv("PYTHONPATH")
if py_path:
    full_path = (Path(__file__).resolve() / py_path).resolve()
    if str(full_path) not in sys.path:
        sys.path.append(str(full_path))

# --- FastAPIアプリケーションのインスタンス作成（環境変数で上書き可）
app = FastAPI(
    title=os.getenv("API_TITLE", "RAG_API"),
    version=os.getenv("API_VERSION", "1.0.0"),
    root_path=os.getenv("API_ROOT_PATH", "/rag_api"),
    docs_url=os.getenv("API_DOCS_URL", "/docs"),
    openapi_url=os.getenv("API_OPENAPI_URL", "/openapi.json"),
)

# --- バリデーションエラー時のカスタムレスポンス ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "リクエストの形式が正しくありません。",
            "detail": exc.errors()
        }
    )

# --- CORS設定（環境変数で上書き可）
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- APIルーター登録（拡張しやすいリスト構造）
routers = [
    (query.router, "/api"),
    # 追加ルーターはここにタプルで追記
]
for router, prefix in routers:
    app.include_router(router, prefix=prefix)

# --- 動作確認用のルート
@app.get("/")
async def root():
    return {"message": "Welcome to the Sanbo Navi API"}
