"""
Core API - BFF/Facade for frontend.
Handles short sync calls and job queuing for long-running tasks.
"""
import logging
import os
from pythonjsonlogger import jsonlogger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import ingest, forecast, kpi, external, calendar, reports, chat, analysis, database, block_unit_price, manual

# Setup structured JSON logging
logger = logging.getLogger()
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter("%(asctime)s %(name)s %(levelname)s %(message)s")
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# FastAPI application
app = FastAPI(
    title="Core API",
    description="BFF/Facade API for frontend - handles sync calls and job queuing",
    version="1.0.0",
    root_path=os.getenv("ROOT_PATH", "/api"),
)

# CORS (for dev mode, if needed)
if os.getenv("ENABLE_CORS", "false").lower() == "true":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Register routers
app.include_router(ingest.router)
app.include_router(forecast.router)
app.include_router(kpi.router)
app.include_router(external.router)
app.include_router(calendar.router)
app.include_router(reports.router)   # BFF: ledger_api reports proxy
app.include_router(block_unit_price.router)  # BFF: ledger_api block_unit_price_interactive proxy (separate from reports)
app.include_router(manual.router)    # BFF: manual_api proxy
app.include_router(chat.router)      # BFF: rag_api chat proxy
app.include_router(analysis.router)  # BFF: ledger_api analysis proxy (TODO: 未実装)
app.include_router(database.router)  # BFF: sql_api database proxy (TODO: 未実装)


@app.get("/healthz", include_in_schema=False, tags=["health"])
@app.get("/health", include_in_schema=False, tags=["health"])
def healthz():
    """
    Health check endpoint.
    Returns 200 if the API is running.
    """
    return {"status": "ok", "service": "core_api"}


@app.get("/", tags=["info"])
def root():
    """
    Root endpoint with API info.
    """
    return {
        "service": "core_api",
        "version": "1.0.0",
        "description": "BFF/Facade API for frontend",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
