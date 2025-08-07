"""
帳票・日報管理システムのメインアプリケーション

このモジュールはFastAPIを使用した帳票生成、日報管理、PDF出力機能を提供するAPIサーバーです。
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import manage_report
from app.api.endpoints.block_unit_price_interactive import (
    router as block_unit_price_router,
)

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
app.include_router(block_unit_price_router, prefix="/block_unit_price")


@app.get("/")
def health_check():
    """
    アプリケーションのヘルスチェックエンドポイント

    Returns:
        dict: アプリケーションの稼働状況
    """
    return {"status": "ledger_api is running"}
