from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import manage_report

app = FastAPI(
    title="帳票・日報API",
    description="帳票生成、日報管理、PDF出力に関するAPI群です。",
    version="1.0.0",
    root_path="/ledger_api",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ルーター登録
app.include_router(manage_report.router)


@app.get("/")
def health_check():
    return {"status": "ledger_api is running"}
