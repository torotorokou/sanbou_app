"""
通知配信API（SSE: Server-Sent Events）

目的:
- NotificationEvent をリアルタイム配信
- クライアントはイベントストリームを購読
"""

import asyncio
import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from backend_shared.core.domain import NotificationEvent


router = APIRouter(prefix="/notifications", tags=["Notifications"])


async def notification_generator():
    """
    通知イベントを定期的に生成するジェネレーター（サンプル実装）

    本番環境では Redis Pub/Sub や Message Queue から受信
    """
    # サンプル通知を定期的に送信
    count = 0
    while True:
        # 5秒ごとにサンプル通知を送信
        await asyncio.sleep(5)
        count += 1

        # NotificationEvent を生成
        event = NotificationEvent(
            id=str(uuid.uuid4()),
            severity="info" if count % 2 == 0 else "success",
            title=f"サンプル通知 #{count}",
            message=f"これは{count}番目のサンプル通知です",
            duration=5000,
            feature="notification_test",
            createdAt=datetime.utcnow().isoformat(),
        )

        # SSE形式で送信
        # event: notification
        # data: <JSON>
        data = event.model_dump(by_alias=True)
        yield "event: notification\n"
        yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.get("/stream")
async def notification_stream(request: Request):
    """
    通知ストリーム（SSE）

    クライアント側:
    ```typescript
    const eventSource = new EventSource('/ledger_api/notifications/stream');
    eventSource.addEventListener('notification', (event) => {
      const notification = JSON.parse(event.data);
      // 通知を表示
    });
    ```

    レスポンス:
    - Content-Type: text/event-stream
    - イベント形式:
      ```
      event: notification
      data: {"id": "...", "severity": "info", "title": "...", ...}
      ```
    """
    return StreamingResponse(
        notification_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Nginx のバッファリングを無効化
        },
    )
