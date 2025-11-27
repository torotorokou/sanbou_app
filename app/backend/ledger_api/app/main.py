"""
帳票・日報管理システムのメインアプリケーション

このモジュールはFastAPIを使用した帳票生成、日報管理、PDF出力機能を提供するAPIサーバーです。
"""

# --- Optional: provide a lightweight stub for `streamlit` in server runtime ---
try:  # pragma: no cover
    import streamlit as _  # type: ignore  # noqa: F401
except Exception:  # if not available, inject stub module
    import importlib
    import sys as _sys

    try:
        _sys.modules["streamlit"] = importlib.import_module("app.streamlit")
    except Exception:
        # If stub missing, ignore; only interactive pages require it
        pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend_shared.infrastructure.logging_utils import setup_uvicorn_access_filter
from backend_shared.adapters.middleware import RequestIdMiddleware
from backend_shared.adapters.fastapi import register_error_handlers

from app.presentation.api.routers.reports.block_unit_price_interactive import (
    router as block_unit_price_router,
)
from app.presentation.api.routers.report_artifacts import router as report_artifact_router
from app.presentation.api.routers.reports import reports_router
from app.presentation.api.routers.jobs import router as jobs_router
from app.presentation.api.routers.notifications import router as notifications_router
from app.settings import settings

# FastAPIアプリケーションの初期化
# NOTE:
#   DIP（依存性逆転の原則）に従い、ledger_api は /ledger_api プレフィックスの存在を知らない。
#   内部論理パス（/reports/..., /block_unit_price_interactive/...）でエンドポイントを公開し、
#   core_api（BFF）が /core_api プレフィックスを付与して外部に公開する。
app = FastAPI(
    title="帳票・日報API",
    description="帳票生成、日報管理、PDF出力に関するAPI群です。内部論理パスで公開。",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ミドルウェア: Request ID（traceId）の付与
app.add_middleware(RequestIdMiddleware)

# CORS設定 - すべてのオリジンからのアクセスを許可
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切なオリジンを指定すること
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],  # X-Request-ID をフロントエンドに公開
)

# エラーハンドラの登録（ProblemDetails統一）
register_error_handlers(app)

# アクセスログ: /health だけ抑制（uvicorn.access にフィルター追加）
setup_uvicorn_access_filter(excluded_paths=("/health",))


# ルーター登録 - 内部論理パスで公開（core_api BFFが /core_api を付与）
app.include_router(
    block_unit_price_router, prefix="/block_unit_price_interactive"
)
app.include_router(reports_router, prefix="/reports")
app.include_router(jobs_router, prefix="")  # /api/jobs
app.include_router(notifications_router, prefix="")  # /notifications


artifact_prefix = settings.report_artifact_url_prefix.rstrip("/") or "/reports/artifacts"
if not artifact_prefix.startswith("/"):
    artifact_prefix = f"/{artifact_prefix}"
app.include_router(
    report_artifact_router,
    prefix=artifact_prefix,
    tags=["Report Artifacts"],
)


@app.get("/")
def health_check():
    """
    アプリケーションのヘルスチェックエンドポイント

    Returns:
        dict: アプリケーションの稼働状況
    """
    return {"status": "ledger_api is running"}


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}

# 互換性: 旧 root_path=/ledger_api 時代のルート ( /ledger_api/ ) にヘルスを返す
@app.get("/ledger_api/", include_in_schema=False)
def legacy_root_health():  # pragma: no cover - 簡易互換
    return {"status": "ledger_api is running"}

