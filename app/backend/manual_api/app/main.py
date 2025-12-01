import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.api.routers.manuals import router as manuals_router
from backend_shared.core.domain.exceptions import (
    DomainException,
    ValidationError,
    NotFoundError,
    BusinessRuleViolation,
    UnauthorizedError,
    ForbiddenError,
    InfrastructureError,
    ExternalServiceError,
)

app = FastAPI(
    title=os.getenv("API_TITLE", "MANUAL_API"),
    version=os.getenv("API_VERSION", "1.0.0"),
    # DIP: manual_apiは/core_apiの存在を知らない。内部論理パスで公開。
    root_path=os.getenv("API_ROOT_PATH", ""),
)

# Exception handlers for backend_shared exceptions
@app.exception_handler(NotFoundError)
async def handle_not_found_error(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "NOT_FOUND",
                "message": exc.message,
                "entity": exc.entity,
                "entity_id": str(exc.entity_id),
            }
        },
    )

@app.exception_handler(ValidationError)
async def handle_validation_error(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": exc.message,
                "field": exc.field,
            }
        },
    )

@app.exception_handler(BusinessRuleViolation)
async def handle_business_rule_violation(request: Request, exc: BusinessRuleViolation):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "BUSINESS_RULE_VIOLATION",
                "message": f"Business rule violated: {exc.rule}",
                "rule": exc.rule,
                "details": exc.details,
            }
        },
    )

@app.exception_handler(InfrastructureError)
async def handle_infrastructure_error(request: Request, exc: InfrastructureError):
    return JSONResponse(
        status_code=503,
        content={
            "error": {
                "code": "INFRASTRUCTURE_ERROR",
                "message": exc.message,
            }
        },
    )

@app.exception_handler(ExternalServiceError)
async def handle_external_service_error(request: Request, exc: ExternalServiceError):
    status_code = 502 if exc.status_code is None else (504 if exc.status_code >= 500 else 502)
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": "EXTERNAL_SERVICE_ERROR",
                "message": f"{exc.service_name}: {exc.message}",
                "service": exc.service_name,
                "status_code": exc.status_code,
            }
        },
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
