"""
Request ID / Trace ID ミドルウェア

【概要】
すべてのHTTPリクエストに一意のRequest IDを付与し、
ログとレスポンスヘッダーに含めることで、リクエストの追跡を可能にします。

【主な機能】
1. Request ID の自動生成 or ヘッダーからの継承
2. ContextVar へのRequest ID設定（ログに自動付与）
3. レスポンスヘッダーへのRequest ID追加
4. request.state へのRequest ID保存（エラーハンドラ等から参照可能）

【設計方針】
- X-Request-ID ヘッダーがあれば使用（外部からのトレーシング継続）
- なければ UUID v4 を生成
- ContextVar 経由で logging と統合
- レスポンスヘッダーに必ず付与（クライアント側でのトレーシング）

【使用例】
```python
from fastapi import FastAPI, Request
from backend_shared.infra.adapters.middleware import RequestIdMiddleware

app = FastAPI()
app.add_middleware(RequestIdMiddleware)

@app.get("/api/test")
async def test(request: Request):
    # request.state.trace_id でアクセス可能
    request_id = request.state.trace_id
    return {"request_id": request_id}
```
"""
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# backend_shared.application.logging から set_request_id をインポート
try:
    from backend_shared.application.logging import set_request_id
    HAS_LOGGING_INTEGRATION = True
except ImportError:
    # logging統合がない場合はスキップ（後方互換性）
    HAS_LOGGING_INTEGRATION = False


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Request ID ミドルウェア
    
    Description:
        各HTTPリクエストにユニークなRequest IDを付与し、
        ログとレスポンスに含めることでトレーシングを実現します。
        
    Processing Flow:
        1. X-Request-ID ヘッダーを確認
        2. なければ新規 UUID を生成
        3. ContextVar に設定（logging Filter で使用）
        4. request.state に保存（エンドポイント/エラーハンドラで使用）
        5. 次のミドルウェア/エンドポイントへ処理を渡す
        6. レスポンスヘッダーに X-Request-ID を追加
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        ミドルウェアの処理本体
        
        Args:
            request: FastAPI Request
            call_next: 次の処理を呼び出すコールバック
            
        Returns:
            Response: レスポンス（X-Request-ID ヘッダー付き）
        """
        # ========================================
        # 1. Request ID の取得 or 生成
        # ========================================
        # X-Request-ID ヘッダーがあれば使用（外部サービスからのトレーシング継続）
        # なければ新規 UUID を生成
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # ========================================
        # 2. ContextVar に設定（logging 統合）
        # ========================================
        # これにより、以降の全ログに自動的に request_id が付与される
        if HAS_LOGGING_INTEGRATION:
            set_request_id(request_id)
        
        # ========================================
        # 3. request.state に保存
        # ========================================
        # エンドポイント内や error_handler からアクセス可能にする
        # 既存コードとの互換性のため trace_id としても保存
        request.state.request_id = request_id
        request.state.trace_id = request_id  # 後方互換性
        
        # ========================================
        # 4. 次の処理へ（エンドポイント実行）
        # ========================================
        response: Response = await call_next(request)
        
        # ========================================
        # 5. レスポンスヘッダーに追加
        # ========================================
        # クライアント側でもRequest IDを確認できるようにする
        response.headers["X-Request-ID"] = request_id
        
        return response
