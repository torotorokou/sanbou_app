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

from app.api.endpoints import manage_report
from app.api.endpoints.block_unit_price_interactive import (
    router as block_unit_price_router,
)
from app.api.endpoints.reports import reports_router

# FastAPIアプリケーションの初期化
app = FastAPI(
    title="帳票・日報API",
    description="帳票生成、日報管理、PDF出力に関するAPI群です。",
    version="1.0.0",
    root_path="/ledger_api",
)

# CORS設定 - すべてのオリジンからのアクセスを許可
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切なオリジンを指定すること
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ルーター登録 - 各機能のエンドポイントを追加
app.include_router(manage_report.router)
app.include_router(block_unit_price_router, prefix="/block_unit_price_interactive")
app.include_router(reports_router, prefix="/reports")


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
