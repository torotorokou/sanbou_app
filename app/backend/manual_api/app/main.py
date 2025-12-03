import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

# ==========================================
# 統一ロギング設定のインポート（backend_shared）
# ==========================================
from backend_shared.application.logging import setup_logging
from backend_shared.infra.frameworks.logging_utils import setup_uvicorn_access_filter
from backend_shared.infra.adapters.middleware import RequestIdMiddleware
from backend_shared.config.env_utils import is_debug_mode

from app.api.routers.manuals import router as manuals_router
from backend_shared.core.domain.exceptions import (
    DomainException,
    ValidationError,
    NotFoundError,
    BusinessRuleViolation,
    UnauthorizedError,
    ForbiddenError,
    InfrastructureError,
    ExternalServiceError,
)

# ==========================================
# 統一ロギング設定の初期化
# ==========================================
# テクニカルログ基盤: JSON形式、Request ID付与、Uvicorn統合
# 環境変数 LOG_LEVEL で制御可能（DEBUG/INFO/WARNING/ERROR/CRITICAL）
setup_logging()

from backend_shared.application.logging import get_module_logger
logger = get_module_logger(__name__)

# DEBUG モード判定（共通ユーティリティ使用）
DEBUG = is_debug_mode()

app = FastAPI(
    title=os.getenv("API_TITLE", "MANUAL_API"),
    version=os.getenv("API_VERSION", "1.0.0"),
    # DIP: manual_apiは/core_apiの存在を知らない。内部論理パスで公開。
    root_path=os.getenv("API_ROOT_PATH", ""),
    # 本番環境（DEBUG=False）では /docs と /redoc を無効化
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None,
    openapi_url="/openapi.json" if DEBUG else None,
)

logger.info(
    f"Manual API initialized (DEBUG={DEBUG}, docs_enabled={DEBUG})",
    extra={"operation": "app_init", "debug": DEBUG}
)

# --- ミドルウェア: Request ID追跡 ----------------------------------------------
# 統一ロギング基盤: HTTPリクエストごとに一意のrequest_idを割り当て、ContextVarで管理
# 全ログ出力にrequest_idが付与され、分散トレーシングが可能になる
app.add_middleware(RequestIdMiddleware)

# Exception handlers for backend_shared exceptions
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

@app.exception_handler(BusinessRuleViolation)
async def handle_business_rule_violation(request: Request, exc: BusinessRuleViolation):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "BUSINESS_RULE_VIOLATION",
                "message": f"Business rule violated: {exc.rule}",
                "rule": exc.rule,
                "details": exc.details,
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

@app.exception_handler(ExternalServiceError)
async def handle_external_service_error(request: Request, exc: ExternalServiceError):
    status_code = 502 if exc.status_code is None else (504 if exc.status_code >= 500 else 502)
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": "EXTERNAL_SERVICE_ERROR",
                "message": f"{exc.service_name}: {exc.message}",
                "service": exc.service_name,
                "status_code": exc.status_code,
            }
        },
    )

origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
