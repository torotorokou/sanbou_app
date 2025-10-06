"""
Request ID / Trace ID ミドルウェア

目的:
- すべてのリクエストに一意のトレースIDを付与
- X-Request-ID ヘッダーから読み取り、または自動生成
- レスポンスヘッダーに X-Request-ID を追加
- request.state.trace_id でアプリケーション全体から参照可能
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import uuid


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    リクエストIDミドルウェア
    
    機能:
    - リクエストヘッダから X-Request-ID を取得、なければ生成
    - request.state.trace_id に保存
    - レスポンスヘッダに X-Request-ID を追加
    """
    
    async def dispatch(self, request: Request, call_next):
        # X-Request-ID を取得、なければ新規生成
        rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # request.state に保存（エラーハンドラ等から参照可能）
        request.state.trace_id = rid
        
        # 次の処理へ
        response: Response = await call_next(request)
        
        # レスポンスヘッダに追加
        response.headers["X-Request-ID"] = rid
        
        return response
