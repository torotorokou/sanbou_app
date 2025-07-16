from fastapi import FastAPI
from app.api.api_router import api_router

app = FastAPI(
    title="SQL帳簿API",
    description="CSVからの帳簿変換、補完、保存、ダッシュボード連携などのSQL操作APIです。",
    version="1.0.0",
    root_path="/sql",
    docs_url="/docs",
    openapi_url="/openapi.json",
    redoc_url=None,
)

app.include_router(api_router, prefix="/api")  # 👈 ここが集約ポイント


@app.get("/ping")
def ping():
    return {"status": "sql ok"}
