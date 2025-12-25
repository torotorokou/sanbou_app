import os
from pathlib import Path

from app.api.routers.manuals import router as manuals_router
from app.config.settings import settings

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
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# ==========================================
# 統一ロギング設定の初期化
# ==========================================
# テクニカルログ基盤: JSON形式、Request ID付与、Uvicorn統合
# 環境変数 LOG_LEVEL で制御可能（DEBUG/INFO/WARNING/ERROR/CRITICAL）
setup_logging()

from backend_shared.application.logging import get_module_logger

logger = get_module_logger(__name__)

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    # DIP: manual_apiは/core_apiの存在を知らない。内部論理パスで公開。
    root_path=settings.API_ROOT_PATH,
    # 本番環境（DEBUG=False）では /docs と /redoc を無効化
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

logger.info(
    f"Manual API initialized (DEBUG={settings.DEBUG}, docs_enabled={settings.DEBUG})",
    extra={"operation": "app_init", "debug": settings.DEBUG},
)

# --- ミドルウェア: Request ID追跡 ----------------------------------------------
# 統一ロギング基盤: HTTPリクエストごとに一意のrequest_idを割り当て、ContextVarで管理
# 全ログ出力にrequest_idが付与され、分散トレーシングが可能になる
app.add_middleware(RequestIdMiddleware)

# --- エラーハンドラ登録 (backend_shared統一版) ---------------------------------
register_exception_handlers(app)

# --- CORS設定 (backend_shared統一版) -----------------------------------------
setup_cors(app)

data_dir = Path(__file__).resolve().parent.parent / "data"
if data_dir.exists():
    # Serve manual static assets under internal logical path
    # BFF (core_api) will add /core_api prefix when exposing to frontend
    app.mount("/manual/assets", StaticFiles(directory=data_dir), name="manual-assets")

app.include_router(manuals_router, prefix="/manual")


@app.get("/__health")
@app.get("/health")
def health():
    return {"ok": True, "service": "manual_api"}
