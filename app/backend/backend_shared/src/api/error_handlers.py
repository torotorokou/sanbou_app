"""
統一エラーハンドラ（ProblemDetails準拠）

目的:
- すべてのエラーを ProblemDetails 形式で返す
- traceId を自動付与
- ドメインエラー/予期しないエラーを区別

契約:
- contracts/notifications.openapi.yaml の ProblemDetails に準拠
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from backend_shared.src.domain.contract import ProblemDetails


class DomainError(Exception):
    """
    ドメインエラー（ビジネスロジック層のエラー）
    
    使用例:
        raise DomainError(
            code="VALIDATION_ERROR",
            status=422,
            user_message="入力値が不正です",
            title="バリデーションエラー"
        )
    """
    
    def __init__(
        self,
        code: str,
        status: int,
        user_message: str,
        title: str | None = None,
        trace_id: str | None = None,
    ):
        self.code = code
        self.status = status
        self.user_message = user_message
        self.title = title or "Application error"
        self.trace_id = trace_id
        super().__init__(user_message)


async def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
    """
    ドメインエラーハンドラ
    
    ProblemDetails 形式でエラーを返す
    """
    # traceId を取得（例外に含まれるか、request.state から）
    trace_id = exc.trace_id or getattr(request.state, "trace_id", None)
    
    # ProblemDetails を作成
    pd = ProblemDetails(
        status=exc.status,
        code=exc.code,
        userMessage=exc.user_message,
        title=exc.title,
        traceId=trace_id,
    )
    
    return JSONResponse(
        status_code=exc.status,
        content=pd.model_dump(by_alias=True),  # camelCase で出力
    )


async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
    """
    予期しないエラーハンドラ
    
    500 Internal Server Error として ProblemDetails を返す
    """
    trace_id = getattr(request.state, "trace_id", None)
    
    pd = ProblemDetails(
        status=500,
        code="INTERNAL_ERROR",
        userMessage="処理に失敗しました。時間をおいて再試行してください。",
        title="Unexpected error",
        traceId=trace_id,
    )
    
    # ログ出力（本番環境では詳細を記録）
    import logging
    logger = logging.getLogger(__name__)
    logger.exception(f"Unexpected error [traceId={trace_id}]", exc_info=exc)
    
    return JSONResponse(
        status_code=500,
        content=pd.model_dump(by_alias=True),
    )


def register_error_handlers(app):
    """
    エラーハンドラを登録
    
    使用例:
        from backend_shared.src.api.error_handlers import register_error_handlers
        
        app = FastAPI()
        register_error_handlers(app)
    """
    app.add_exception_handler(DomainError, handle_domain_error)
    app.add_exception_handler(Exception, handle_unexpected)
