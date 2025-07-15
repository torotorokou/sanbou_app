from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ルーターを使う場合（あとで追加）
# from app.api import daily_report

app = FastAPI(
    title="Ledger API",
    description="帳票・日報・集計などを処理するバックエンドAPI",
    version="0.1.0",
)

# CORS設定（必要に応じて調整）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番では絞ってください
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録（例: /daily-report）
# app.include_router(daily_report.router)


@app.get("/")
def health_check():
    return {"status": "ledger_api is running"}
