"""
FastAPIアプリケーションのエントリポイント。
初心者にも分かりやすいように日本語でコメント・ドックストリングを記載しています。
"""

from fastapi import FastAPI
from app.api.endpoints.syogun_csv_upload import router as upload_router
# from app.api.data_api import data_router


# FastAPIアプリケーションのインスタンスを作成
app = FastAPI(
    title="SQL帳簿API",
    version="1.0.0",
    root_path="/sql_api",  # API全体のベースパスを指定
    docs_url="/docs",
    openapi_url="/openapi.json",
)


# アップロード関連のAPIを /upload 以下にまとめる
app.include_router(upload_router, prefix="/upload")


# データ取得関連のAPIを /data 以下にまとめる
# app.include_router(data_router, prefix="/data")


@app.get("/ping")
def ping():
    """
    動作確認用のエンドポイント。
    /ping にアクセスするとAPIの稼働状況を返します。
    """
    return {"status": "sql_api ok"}


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}
