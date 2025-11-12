"""
Core API - BFF/Facade for frontend.
Handles short sync calls and job queuing for long-running tasks.
"""
import logging
import os
from pythonjsonlogger import jsonlogger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.presentation.routers.ingest.router import router as ingest_router
from app.presentation.routers.forecast.router import router as forecast_router
from app.presentation.routers.kpi.router import router as kpi_router
from app.presentation.routers.external.router import router as external_router
from app.presentation.routers.calendar.router import router as calendar_router
from app.presentation.routers.reports.router import router as reports_router
from app.presentation.routers.chat.router import router as chat_router
from app.presentation.routers.analysis.router import router as analysis_router
from app.presentation.routers.database.router import router as database_router
from app.presentation.routers.block_unit_price.router import router as block_unit_price_router
from app.presentation.routers.manual.router import router as manual_router
from app.presentation.routers.dashboard.router import router as dashboard_router
from app.presentation.routers.inbound.router import router as inbound_router

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
app.include_router(ingest_router)
app.include_router(forecast_router)
app.include_router(kpi_router)
app.include_router(external_router)
app.include_router(calendar_router)
app.include_router(reports_router)   # BFF: ledger_api reports proxy
app.include_router(block_unit_price_router)  # BFF: ledger_api block_unit_price_interactive proxy (separate from reports)
app.include_router(manual_router)    # BFF: manual_api proxy
app.include_router(chat_router)      # BFF: rag_api chat proxy
app.include_router(analysis_router)  # BFF: ledger_api analysis proxy (TODO: 未実装)
app.include_router(database_router)  # BFF: sql_api database proxy (TODO: 未実装)
app.include_router(dashboard_router) # Dashboard: target metrics
app.include_router(inbound_router)   # Inbound: daily data with cumulative


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
