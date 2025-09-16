import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from backend_shared.src.logging_utils import setup_uvicorn_access_filter
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.paths import CONFIG_ENV
from app.utils.env_loader import load_env_and_secrets
from app.api.endpoints import query  # ← query.py に router を定義


# --- .env + secrets 読み込み --------------------------------------------------
load_dotenv(dotenv_path=CONFIG_ENV)
_secrets_file = load_env_and_secrets()
print(f"[DEBUG] secrets loaded from: {_secrets_file}")

# --- PYTHONPATH 追加（任意） ---------------------------------------------------
py_path = os.getenv("PYTHONPATH")
if py_path:
    full_path = (Path(__file__).resolve() / py_path).resolve()
    if str(full_path) not in sys.path:
        sys.path.append(str(full_path))

# --- FastAPI アプリ作成（root_path は本番の reverse proxy 下でのみ設定） -----
app = FastAPI(
    title=os.getenv("API_TITLE", "RAG_API"),
    version=os.getenv("API_VERSION", "1.0.0"),
    # 直叩きで 404 を避けるためデフォルトは空文字。Nginx配下では .env で /rag_api を指定
    root_path=os.getenv("API_ROOT_PATH", "/rag_api"),
    docs_url=os.getenv("API_DOCS_URL", "/docs"),
    openapi_url=os.getenv("API_OPENAPI_URL", "/openapi.json"),
)

# --- 静的配信: /pdfs ----------------------------------------------------------
PDF_DIR = Path("/backend/static/pdfs")
PDF_DIR.mkdir(parents=True, exist_ok=True)
print(f"[DEBUG] FastAPI公開ディレクトリ: {PDF_DIR}")
app.mount("/pdfs", StaticFiles(directory=str(PDF_DIR)), name="pdfs")

# （任意）テスト用ディレクトリ /test_pdfs も配信
TEST_PDF_DIR = Path("/backend/static/test_pdfs")
TEST_PDF_DIR.mkdir(parents=True, exist_ok=True)
print(f"[DEBUG] FastAPI公開ディレクトリ: {TEST_PDF_DIR}")
app.mount("/test_pdfs", StaticFiles(directory=str(TEST_PDF_DIR)), name="test_pdfs")


# --- バリデーションエラー時のカスタムレスポンス -------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "リクエストの形式が正しくありません。",
            "detail": exc.errors(),
        },
    )


# --- CORS 設定 -----------------------------------------------------------------
# デフォルトで Vite (5173) を許可。必要に応じて .env の CORS_ORIGINS で上書き
default_origins = "http://localhost:5173,http://127.0.0.1:5173"
origins = os.getenv("CORS_ORIGINS", default_origins).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# アクセスログ: /health のアクセスのみ抑制（uvicorn.access フィルター）
setup_uvicorn_access_filter(excluded_paths=("/health",))

# --- ルーター登録（mount より後に置かないと競合しない） -----------------------
routers = [
    (query.router, "/api"),
    # 追加ルーターがあればここに追記
]
for router, prefix in routers:
    app.include_router(router, prefix=prefix)


# --- 確認用エンドポイント -----------------------------------------------------
@app.get("/__health")
def __health():
    """疎通確認用"""
    return {"ok": True}


@app.get("/__exists")
def __exists():
    """PDFディレクトリの存在と一覧を返す（デバッグ用）"""
    try:
        files = sorted(os.listdir(PDF_DIR))
        return {"dir": str(PDF_DIR), "exists": PDF_DIR.exists(), "files": files}
    except Exception as e:
        return JSONResponse({"dir": str(PDF_DIR), "error": repr(e)}, status_code=500)


@app.get("/api/pdf/{name}")
def get_pdf(name: str):
    """
    StaticFiles を経由せずに個別 PDF を返す回避策（当面の運用にも使用可）。
    name は英数字テスト推奨（日本語名は URL エンコードが必要）。
    """
    p = (PDF_DIR / name).resolve()
    if not p.is_file() or p.parent != PDF_DIR.resolve():
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(str(p), media_type="application/pdf", filename=name)


# --- ルート --------------------------------------------------------------------
@app.get("/")
async def root():
    return {"message": "Welcome to the Sanbo Navi API"}


# --- health (for docker compose) ---
@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}
