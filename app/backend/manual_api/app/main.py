import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import router as manuals_router

app = FastAPI(
    title=os.getenv("API_TITLE", "MANUAL_API"),
    version=os.getenv("API_VERSION", "1.0.0"),
    # DIP: manual_apiは/core_apiの存在を知らない。内部論理パスで公開。
    root_path=os.getenv("API_ROOT_PATH", ""),
)

origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

data_dir = Path(__file__).resolve().parent.parent / "data"
if data_dir.exists():
    # Serve manual static assets under internal logical path
    # BFF (core_api) will add /core_api prefix when exposing to frontend
    app.mount("/manual/assets", StaticFiles(directory=data_dir), name="manual-assets")

app.include_router(manuals_router, prefix="/manual")

@app.get("/__health")
@app.get("/health")
def health():
    return {"ok": True, "service": "manual_api"}
