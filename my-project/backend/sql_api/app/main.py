from fastapi import FastAPI
from app.api.endpoints import vendors  # ← vendors.pyのrouterをインポート

# FastAPIインスタンス作成
app = FastAPI(
    title="SQL帳簿API",
    description="CSVからの帳簿変換、補完、保存、ダッシュボード連携などのSQL操作APIです。",
    version="1.0.0",
    root_path="/sql",
    docs_url="/docs",
    openapi_url="/openapi.json",
    redoc_url=None  # 使わない場合は明示的に無効化
)


# CORS設定（必要に応じて調整）
@app.get("/ping")
def ping():
    return {"status": "sql ok"}


import logging
logging.basicConfig(level=logging.INFO)
print("✅ FastAPI started with root_path = /sql")