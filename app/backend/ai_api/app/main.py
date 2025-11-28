from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend_shared.infra.frameworks.logging_utils import setup_uvicorn_access_filter
from backend_shared.core.domain.exceptions import ExternalServiceError, InfrastructureError
from app.api.routers import chat

app = FastAPI(
    title="AI 応答API",
    description="PDF連動のAI応答や自然言語処理を提供するAPI群です。",
    version="1.0.0",
    root_path="/ai_api",  # ベースパスを統一
)

# Exception handlers for backend_shared exceptions
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

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ログ設定: /health のアクセスログのみ抑制（エラーは従来通り出力）
setup_uvicorn_access_filter(excluded_paths=("/health",))

# ====== ルーターをパス指定で登録 ======
app.include_router(chat.router, prefix="")  # /ai_api直下に登録


# ヘルスチェック
@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}

