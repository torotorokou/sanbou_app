import os
import sys
from pathlib import Path

# ==========================================
# 統一ロギング設定のインポート（backend_shared）
# ==========================================
from backend_shared.application.logging import setup_logging
from backend_shared.infra.adapters.middleware import RequestIdMiddleware
from backend_shared.infra.frameworks.cors_config import setup_cors
from backend_shared.infra.frameworks.exception_handlers import (
    register_exception_handlers,
)
from backend_shared.infra.frameworks.logging_utils import setup_uvicorn_access_filter
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routers import manuals, query  # ← query.py に router を定義
from app.config.paths import CONFIG_ENV
from app.config.settings import settings
from app.shared.env_loader import load_env_and_secrets

# --- .env + secrets 読み込み --------------------------------------------------
load_dotenv(dotenv_path=CONFIG_ENV)
_secrets_file = load_env_and_secrets()

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
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="オブジェクト廃棄物マニュアルQA & 全文検索システム",
    # 直叩きで 404 を避けるためデフォルトは空文字。Nginx配下では .env で /rag_api を指定
    root_path=settings.API_ROOT_PATH,
    # 本番環境（DEBUG=False）では /docs と /redoc を無効化
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

from backend_shared.application.logging import get_module_logger

logger = get_module_logger(__name__)
logger.info(
    f"RAG API initialized (DEBUG={settings.DEBUG}, docs_enabled={settings.DEBUG})",
    extra={"operation": "app_init", "debug": settings.DEBUG},
)

# --- GCP認証・権限デバッグ（起動時1回のみ実行） ---------------------------------
if settings.STAGE in ("stg", "prod") and settings.PERMISSION_DEBUG:
    logger.info("🔍 PERMISSION_DEBUG=1 が有効なため、GCP認証デバッグを実行します")
    from app.infra.adapters.gcp import debug_log_gcp_adc_and_permissions

    debug_log_gcp_adc_and_permissions(
        bucket_name=settings.GCS_BUCKET_NAME, object_prefix=settings.GCS_DATA_PREFIX
    )

# --- ミドルウェア: Request ID追跡 ----------------------------------------------
# 統一ロギング基盤: HTTPリクエストごとに一意のrequest_idを割り当て、ContextVarで管理
# 全ログ出力にrequest_idが付与され、分散トレーシングが可能になる
app.add_middleware(RequestIdMiddleware)

# --- エラーハンドラ登録 (backend_shared統一版) ---------------------------------
register_exception_handlers(app)

# --- 静的配信: /pdfs ----------------------------------------------------------
PDF_DIR = Path("/backend/static/pdfs")
PDF_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/pdfs", StaticFiles(directory=str(PDF_DIR)), name="pdfs")

# （任意）テスト用ディレクトリ /test_pdfs も配信
TEST_PDF_DIR = Path("/backend/static/test_pdfs")
TEST_PDF_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/test_pdfs", StaticFiles(directory=str(TEST_PDF_DIR)), name="test_pdfs")


# --- CORS 設定 -----------------------------------------------------------------
# --- CORS設定 (backend_shared統一版) -----------------------------------------
setup_cors(app)

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
