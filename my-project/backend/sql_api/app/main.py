# sql_api/app/main.py

from fastapi import FastAPI
from app.api.endpoints import router as api_router

app = FastAPI(title="SQL API")

app.include_router(api_router, prefix="/api")
