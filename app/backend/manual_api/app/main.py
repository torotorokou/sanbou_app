import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import router as manuals_router

app = FastAPI(
    title=os.getenv("API_TITLE", "MANUAL_API"),
    version=os.getenv("API_VERSION", "1.0.0"),
    root_path=os.getenv("API_ROOT_PATH", "/manual_api"),
)

origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(manuals_router, prefix="/api")

@app.get("/__health")
def health():
    return {"ok": True}
