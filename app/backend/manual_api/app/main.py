import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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

data_dir = Path(__file__).resolve().parent.parent / "data"
if data_dir.exists():
    # Serve manual static assets under the same base route used by build_manual_asset_url
    # (default: /manual_api/api/assets). This keeps frontend URLs consistent and makes
    # it easy to swap in a GCS-signed-URL provider later.
    app.mount("/manual_api/api/assets", StaticFiles(directory=data_dir), name="manual-assets")

app.include_router(manuals_router, prefix="/api")

@app.get("/__health")
def health():
    return {"ok": True}
