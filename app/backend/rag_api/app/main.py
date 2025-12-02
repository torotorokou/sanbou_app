import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

# ==========================================
# 統一ロギング設定のインポート（backend_shared）
# ==========================================
from backend_shared.application.logging import setup_logging
from backend_shared.infra.frameworks.logging_utils import setup_uvicorn_access_filter
from backend_shared.infra.adapters.middleware import RequestIdMiddleware

from backend_shared.core.domain.exceptions import ValidationError, NotFoundError, InfrastructureError
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.config.paths import CONFIG_ENV
from app.shared.env_loader import load_env_and_secrets
from app.api.routers import query, manuals  # ← query.py に router を定義


# --- .env + secrets 読み込み --------------------------------------------------
load_dotenv(dotenv_path=CONFIG_ENV)
_secrets_file = load_env_and_secrets()
print(f"[DEBUG] secrets loaded from: {_secrets_file}")

# ==========================================
# 統一ロギング設定の初期化
# ==========================================
# テクニカルログ基盤: JSON形式、Request ID付与、Uvicorn統合
# 環境変数 LOG_LEVEL で制御可能（DEBUG/INFO/WARNING/ERROR/CRITICAL）
setup_logging()

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

# --- ミドルウェア: Request ID追跡 ----------------------------------------------
# 統一ロギング基盤: HTTPリクエストごとに一意のrequest_idを割り当て、ContextVarで管理
# 全ログ出力にrequest_idが付与され、分散トレーシングが可能になる
app.add_middleware(RequestIdMiddleware)

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

# --- backend_shared exception handlers -----------------------------------------
@app.exception_handler(ValidationError)
async def handle_validation_error(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": exc.message,
                "field": exc.field,
            }
        },
    )

@app.exception_handler(NotFoundError)
async def handle_not_found_error(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "NOT_FOUND",
                "message": exc.message,
                "entity": exc.entity,
                "entity_id": str(exc.entity_id),
            }
        },
    )

@app.exception_handler(InfrastructureError)
async def handle_infrastructure_error(request: Request, exc: InfrastructureError):
    return JSONResponse(
        status_code=503,
        content={
            "error": {
                "code": "INFRASTRUCTURE_ERROR",
                "message": exc.message,
            }
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
    (manuals.router, "/api"),
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
