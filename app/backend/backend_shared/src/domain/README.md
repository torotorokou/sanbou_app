# Domain契約モジュール

## 概要

OpenAPI仕様に準拠した共通契約モデルを提供します。
フロントエンド・バックエンド間の通信における型安全性を保証します。

## 契約定義

すべての契約は `/contracts/notifications.openapi.yaml` で定義されています。

## モデル

### ProblemDetails

RFC 7807 Problem Details 準拠のエラー情報モデル。

```python
from backend_shared.src.domain import ProblemDetails

problem = ProblemDetails(
    status=422,
    code="VALIDATION_ERROR",
    userMessage="入力値が不正です",
    title="バリデーションエラー",
    traceId="trace-123"
)
```

**フィールド:**
- `status` (必須): HTTPステータスコード
- `code` (必須): アプリケーション固有のエラーコード
- `userMessage` (必須): ユーザー向けメッセージ
- `title` (任意): エラータイトル
- `traceId` (任意): トレースID

### NotificationEvent

通知イベントモデル。WebSocket/SSE経由でフロントエンドに送信されます。

```python
from backend_shared.src.domain import NotificationEvent, Severity
from datetime import datetime
import uuid

notification = NotificationEvent(
    id=str(uuid.uuid4()),
    severity="success",
    title="処理完了",
    message="CSVのアップロードが完了しました",
    duration=5000,  # 5秒後に自動削除
    feature="csv_upload",
    resultUrl="/results/123",
    jobId="job-456",
    traceId="trace-789",
    createdAt=datetime.utcnow().isoformat()
)
```

**フィールド:**
- `id` (必須): UUID形式の通知ID
- `severity` (必須): `success` | `info` | `warning` | `error`
- `title` (必須): 通知タイトル
- `message` (任意): 詳細メッセージ
- `duration` (任意): 表示時間(ms) / `None`=自動削除なし
- `feature` (任意): 機能名
- `resultUrl` (任意): 結果URL
- `jobId` (任意): ジョブID
- `traceId` (任意): トレースID
- `createdAt` (必須): 作成日時(ISO8601)

## 使用例

### API応答での利用

```python
from backend_shared.src.api_response import ApiResponse, ProblemDetails

@app.get("/api/data", response_model=ApiResponse[dict])
async def get_data():
    return ApiResponse.success(
        code="DATA_RETRIEVED",
        detail="データを取得しました",
        result={"items": [...]},
        traceId="trace-123"
    )

@app.post("/api/upload", response_model=ApiResponse[dict])
async def upload_file():
    if validation_failed:
        return ApiResponse.error(
            code="VALIDATION_ERROR",
            detail="ファイル検証に失敗しました",
            hint="ファイル形式を確認してください",
            traceId="trace-456"
        )
```

### ProblemDetails変換

```python
from backend_shared.src.api_response import ApiResponse

error_response = ApiResponse.error(
    code="INVALID_INPUT",
    detail="入力値が不正です",
    hint="必須項目を入力してください",
    traceId="trace-789"
)

# ProblemDetailsに変換
problem_details = error_response.to_problem_details(status_code=422)
```

## フロントエンドとの連携

TypeScript型は `/app/frontend/src/features/notification/model/contract.ts` で定義されています。

```typescript
import type { NotificationEvent, ProblemDetails } from '@/features/notification/model/contract';

// 通知の受信
const notification: NotificationEvent = {
  id: "uuid",
  severity: "success",
  title: "処理完了",
  // ...
};

// エラー情報の処理
const problem: ProblemDetails = {
  status: 422,
  code: "VALIDATION_ERROR",
  userMessage: "入力値が不正です"
};
```

## 注意事項

- `ProblemDetails` は `api_response` モジュールからもインポート可能（後方互換性）
- 新規コードでは `backend_shared.src.domain` からのインポートを推奨
- camelCase/snake_case の両方に対応（Pydantic の `populate_by_name=True`）
