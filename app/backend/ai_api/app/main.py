import os

from app.api.routers import chat
from app.config.settings import settings

# ==========================================
# 統一ロギング設定のインポート（backend_shared）
# ==========================================
from backend_shared.application.logging import get_module_logger, setup_logging
from backend_shared.infra.adapters.middleware import RequestIdMiddleware
from backend_shared.infra.frameworks.cors_config import setup_cors
from backend_shared.infra.frameworks.exception_handlers import (
    register_exception_handlers,
)
from backend_shared.infra.frameworks.logging_utils import setup_uvicorn_access_filter
from fastapi import FastAPI

# ==========================================
# 統一ロギング設定の初期化
# ==========================================
# テクニカルログ基盤: JSON形式、Request ID付与、Uvicorn統合
# 環境変数 LOG_LEVEL で制御可能（DEBUG/INFO/WARNING/ERROR/CRITICAL）
setup_logging()
logger = get_module_logger(__name__)

app = FastAPI(
    title=settings.API_TITLE,
    description="PDF連動のAI応答や自然言語処理を提供するAPI群です。",
    version=settings.API_VERSION,
    root_path="/ai_api",  # ベースパスを統一
    # 本番環境（DEBUG=False）では /docs と /redoc を無効化
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

logger.info(
    f"AI API initialized (DEBUG={settings.DEBUG}, docs_enabled={settings.DEBUG})",
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

# ログ設定: /health のアクセスログのみ抑制（エラーは従来通り出力）
setup_uvicorn_access_filter(excluded_paths=("/health",))

# ====== ルーターをパス指定で登録 ======
app.include_router(chat.router, prefix="")  # /ai_api直下に登録


# ヘルスチェック
@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}
