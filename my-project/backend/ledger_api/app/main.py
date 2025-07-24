from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ルーターを使う場合（あとで追加）
# from app.api import daily_report

app = FastAPI(
    title="帳票・日報API",
    description="帳票生成、日報管理、PDF出力に関するAPI群です。",
    version="1.0.0",
    root_path="/ledger"
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
