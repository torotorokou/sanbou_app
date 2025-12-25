"""
メンテナンス中ページを返すシンプルな FastAPI アプリケーション

すべてのパス/メソッドに対して HTTP 503 (Service Unavailable) を返し、
Retry-After ヘッダで再試行時間を通知します。

本番環境では Cloud Run にデプロイし、IAP + LB 経由でアクセスさせます。
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse


app = FastAPI(title="Maintenance Page", docs_url=None, redoc_url=None)

# メンテナンス中ページの HTML（最小構成、外部リソース依存なし）
MAINTENANCE_HTML = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>メンテナンス中</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                         "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 16px;
            padding: 60px 40px;
            max-width: 600px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            text-align: center;
        }
        .icon {
            font-size: 80px;
            margin-bottom: 20px;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.05); opacity: 0.8; }
        }
        h1 {
            font-size: 32px;
            color: #333;
            margin-bottom: 16px;
            font-weight: 700;
        }
        p {
            font-size: 18px;
            color: #666;
            line-height: 1.6;
            margin-bottom: 12px;
        }
        .note {
            font-size: 14px;
            color: #999;
            margin-top: 30px;
        }
        @media (max-width: 640px) {
            .container {
                padding: 40px 24px;
            }
            h1 {
                font-size: 24px;
            }
            p {
                font-size: 16px;
            }
            .icon {
                font-size: 60px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">🔧</div>
        <h1>メンテナンス中です</h1>
        <p>現在、システムメンテナンスを実施しております。</p>
        <p>しばらくしてから再度アクセスしてください。</p>
        <p class="note">ご不便をおかけして申し訳ございません。</p>
    </div>
</body>
</html>
"""


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def maintenance_handler(request: Request, path: str):
    """
    すべてのパスとメソッドに対して503を返す

    Args:
        request: FastAPI Request オブジェクト
        path: リクエストされたパス

    Returns:
        HTMLResponse: 503 Service Unavailable
    """
    return HTMLResponse(
        content=MAINTENANCE_HTML,
        status_code=503,
        headers={
            "Retry-After": "3600",  # 1時間後に再試行を推奨
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )


@app.get("/health")
async def health_check():
    """
    ヘルスチェック用エンドポイント（Cloud Run が使用）

    Returns:
        dict: ステータス情報
    """
    return {"status": "maintenance_mode", "code": 503}


if __name__ == "__main__":
    import os

    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
