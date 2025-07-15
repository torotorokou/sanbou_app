from fastapi import FastAPI
from app.api.endpoints import vendors  # ← vendors.pyのrouterをインポート

app = FastAPI()
app.include_router(vendors.router)
