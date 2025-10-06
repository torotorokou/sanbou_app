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
from backend_shared.src.logging_utils import setup_uvicorn_access_filter
from backend_shared.src.middleware import RequestIdMiddleware
from backend_shared.src.api import register_error_handlers

from app.api.endpoints.reports.block_unit_price_interactive import (
    router as block_unit_price_router,
)
from app.api.endpoints.report_artifacts import router as report_artifact_router
from app.api.endpoints.reports import reports_router
from app.api.endpoints.jobs import router as jobs_router
from app.api.endpoints.notifications import router as notifications_router
from app.settings import settings

# FastAPIアプリケーションの初期化
# NOTE:
#   以前は FastAPI(root_path="/ledger_api") を使用していたが、
#   Nginx 側でパスをそのまま透過させていたため実リクエストの path が
#   "/ledger_api/..." となり Router 側のマッチ対象 ("/reports/..." 等) と不一致になり 404 発生。
#   root_path は *プロキシ側で /ledger_api を取り除いた上で* X-Forwarded-Prefix 等を渡す場合に利用するのが正しい。
#   本修正では root_path を廃止し、明示的に /ledger_api プレフィックスを各 include_router に付与 + ドキュメント URL を再設定する。
app = FastAPI(
    title="帳票・日報API",
    description="帳票生成、日報管理、PDF出力に関するAPI群です。",
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


# ルーター登録 - 各機能のエンドポイントを追加（フロントは /ledger_api/reports/* に統一）
app.include_router(
    block_unit_price_router, prefix="/ledger_api/block_unit_price_interactive"
)
app.include_router(reports_router, prefix="/ledger_api/reports")
app.include_router(jobs_router, prefix="/ledger_api")  # /ledger_api/api/jobs
app.include_router(notifications_router, prefix="/ledger_api")  # /ledger_api/notifications


artifact_prefix = settings.report_artifact_url_prefix.rstrip("/") or "/ledger_api/reports/artifacts"
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

