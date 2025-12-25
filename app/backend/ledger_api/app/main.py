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

import os

from app.api.routers.jobs import router as jobs_router
from app.api.routers.notifications import router as notifications_router
from app.api.routers.report_artifacts import router as report_artifact_router
from app.api.routers.reports import reports_router
from app.api.routers.reports.block_unit_price_interactive import (
    router as block_unit_price_router,
)
from app.settings import settings

# ==========================================
# 統一ロギング設定のインポート（backend_shared）
# ==========================================
from backend_shared.application.logging import get_module_logger, setup_logging
from backend_shared.config.env_utils import is_debug_mode
from backend_shared.infra.adapters.fastapi import register_error_handlers
from backend_shared.infra.adapters.middleware import RequestIdMiddleware
from backend_shared.infra.frameworks.logging_utils import setup_uvicorn_access_filter
from fastapi import FastAPI

# ==========================================
# 統一ロギング設定の初期化
# ==========================================
# テクニカルログ基盤: JSON形式、Request ID付与、Uvicorn統合
# 環境変数 LOG_LEVEL で制御可能（DEBUG/INFO/WARNING/ERROR/CRITICAL）
setup_logging()
logger = get_module_logger(__name__)

# DEBUG モード判定（共通ユーティリティ使用）
DEBUG = is_debug_mode()

# FastAPIアプリケーションの初期化
# NOTE:
#   DIP（依存性逆転の原則）に従い、ledger_api は /ledger_api プレフィックスの存在を知らない。
#   内部論理パス（/reports/..., /block_unit_price_interactive/...）でエンドポイントを公開し、
#   core_api（BFF）が /core_api プレフィックスを付与して外部に公開する。
app = FastAPI(
    title="帳票・日報API",
    description="帳票生成、日報管理、PDF出力に関するAPI群です。内部論理パスで公開。",
    version="1.0.0",
    # 本番環境（DEBUG=False）では /docs と /redoc を無効化
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None,
    openapi_url="/openapi.json" if DEBUG else None,
)

logger.info(
    f"Ledger API initialized (DEBUG={DEBUG}, docs_enabled={DEBUG})",
    extra={"operation": "app_init", "debug": DEBUG},
)

# ミドルウェア: Request ID（traceId）の付与
app.add_middleware(RequestIdMiddleware)

# CORS設定
from backend_shared.infra.frameworks.cors_config import setup_cors

setup_cors(app)

# エラーハンドラの登録（ProblemDetails統一）
register_error_handlers(app)

# アクセスログ: /health だけ抑制（uvicorn.access にフィルター追加）
setup_uvicorn_access_filter(excluded_paths=("/health",))


# ルーター登録 - 内部論理パスで公開（core_api BFFが /core_api を付与）
app.include_router(block_unit_price_router, prefix="/block_unit_price_interactive")
app.include_router(reports_router, prefix="/reports")
app.include_router(jobs_router, prefix="")  # /api/jobs
app.include_router(notifications_router, prefix="")  # /notifications


artifact_prefix = (
    settings.report_artifact_url_prefix.rstrip("/") or "/reports/artifacts"
)
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
