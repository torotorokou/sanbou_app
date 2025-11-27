"""
Error Handler Middleware - 統一エラーハンドリング

アプリケーション全体で一貫したエラーレスポンスを提供します。
カスタム例外を HTTP ステータスコードにマッピングし、
構造化されたエラーレスポンスを返します。
"""
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.shared.exceptions import (
    ValidationError,
    NotFoundError,
    BusinessRuleViolation,
    InfrastructureError,
    DomainException,
)

logger = logging.getLogger(__name__)


async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
    """
    ドメイン例外のハンドラー
    
    ビジネスルール違反などのドメイン層の例外を適切な HTTP レスポンスに変換します。
    """
    # ValidationError
    if isinstance(exc, ValidationError):
        logger.warning(f"Validation error: {exc.message}, field={exc.field}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": exc.message,
                    "field": exc.field,
                }
            },
        )
    
    # NotFoundError
    if isinstance(exc, NotFoundError):
        logger.info(f"Resource not found: {exc.resource_type} {exc.identifier}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": "NOT_FOUND",
                    "message": exc.message,
                    "resource_type": exc.resource_type,
                    "identifier": str(exc.identifier),
                }
            },
        )
    
    # BusinessRuleViolation
    if isinstance(exc, BusinessRuleViolation):
        logger.warning(f"Business rule violation: {exc.rule}, details={exc.details}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "BUSINESS_RULE_VIOLATION",
                    "message": str(exc),
                    "rule": exc.rule,
                    "details": exc.details,
                }
            },
        )
    
    # 上記以外の DomainException
    logger.error(f"Unhandled domain exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "DOMAIN_ERROR",
                "message": str(exc),
            }
        },
    )


async def infrastructure_exception_handler(request: Request, exc: InfrastructureError) -> JSONResponse:
    """
    インフラストラクチャ例外のハンドラー
    
    DB接続エラーや外部API呼び出しエラーなどを処理します。
    """
    logger.error(f"Infrastructure error: {exc.message}, cause={exc.cause}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": {
                "code": "INFRASTRUCTURE_ERROR",
                "message": "A service is temporarily unavailable. Please try again later.",
                "details": exc.message,
            }
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    FastAPI バリデーションエラーのハンドラー
    
    Pydantic によるリクエストバリデーションエラーを処理します。
    """
    logger.warning(f"Request validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "REQUEST_VALIDATION_ERROR",
                "message": "Invalid request parameters",
                "details": exc.errors(),
            }
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    HTTP 例外のハンドラー
    
    FastAPI/Starlette の HTTPException を処理します。
    """
    logger.info(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "status_code": exc.status_code,
            }
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    予期しない例外のハンドラー
    
    上記以外の全ての例外をキャッチし、500エラーを返します。
    """
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please contact support.",
            }
        },
    )


def register_exception_handlers(app):
    """
    例外ハンドラーを FastAPI アプリケーションに登録
    
    Args:
        app: FastAPI アプリケーションインスタンス
    """
    app.add_exception_handler(DomainException, domain_exception_handler)
    app.add_exception_handler(InfrastructureError, infrastructure_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
    
    logger.info("Exception handlers registered successfully")
