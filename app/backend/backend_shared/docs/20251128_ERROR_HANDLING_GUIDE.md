# エラーハンドリング & トレーシングガイド

## 概要

ProblemDetails（RFC 7807）に準拠した統一エラーハンドリングとリクエストトレーシング機能を提供します。

## 主要コンポーネント

### 1. RequestIdMiddleware

すべてのリクエストに一意のトレースIDを付与します。

**機能:**

- `X-Request-ID` ヘッダーから読み取り、なければ自動生成
- `request.state.trace_id` に保存
- レスポンスヘッダーに `X-Request-ID` を追加

**設定例:**

```python
from backend_shared.src.middleware import RequestIdMiddleware

app.add_middleware(RequestIdMiddleware)
```

### 2. エラーハンドラ

すべてのエラーを ProblemDetails 形式で返します。

**DomainError（ドメインエラー）:**

```python
from backend_shared.src.api import DomainError

raise DomainError(
    code="VALIDATION_ERROR",
    status=422,
    user_message="入力値が不正です",
    title="バリデーションエラー"
)
```

**エラーハンドラの登録:**

```python
from backend_shared.src.api import register_error_handlers

app = FastAPI()
register_error_handlers(app)
```

## ProblemDetails レスポンス形式

エラー時は以下の形式でレスポンスが返されます:

```json
{
  "status": 422,
  "code": "VALIDATION_ERROR",
  "userMessage": "入力値が不正です",
  "title": "バリデーションエラー",
  "traceId": "550e8400-e29b-41d4-a716-446655440000"
}
```

## ジョブAPI

非同期処理のジョブ状態を管理します。失敗時には `error` フィールドに ProblemDetails が含まれます。

### エンドポイント

#### POST /api/jobs

ジョブを作成

**リクエスト:**

```json
{
  "feature": "csv_upload",
  "parameters": {
    "file": "example.csv"
  }
}
```

**レスポンス:**

```json
{
  "id": "job-123",
  "status": "pending",
  "progress": 0,
  "message": "ジョブを作成しました",
  "result": null,
  "error": null,
  "createdAt": "2025-10-06T12:00:00Z",
  "updatedAt": "2025-10-06T12:00:00Z"
}
```

#### GET /api/jobs/{job_id}

ジョブの状態を取得

**成功時:**

```json
{
  "id": "job-123",
  "status": "completed",
  "progress": 100,
  "message": "処理が完了しました",
  "result": {
    "uploadedFiles": 5
  },
  "error": null,
  "createdAt": "2025-10-06T12:00:00Z",
  "updatedAt": "2025-10-06T12:05:00Z"
}
```

**失敗時:**

```json
{
  "id": "job-123",
  "status": "failed",
  "progress": 0,
  "message": "処理に失敗しました",
  "result": null,
  "error": {
    "status": 500,
    "code": "PROCESSING_ERROR",
    "userMessage": "処理中にエラーが発生しました",
    "title": "処理エラー",
    "traceId": "550e8400-e29b-41d4-a716-446655440000"
  },
  "createdAt": "2025-10-06T12:00:00Z",
  "updatedAt": "2025-10-06T12:03:00Z"
}
```

## 使用例

### 1. 基本的なエラーハンドリング

```python
from fastapi import APIRouter, Request
from backend_shared.src.api import DomainError

router = APIRouter()

@router.post("/upload")
async def upload_file(request: Request, file: UploadFile):
    if not file.filename.endswith('.csv'):
        raise DomainError(
            code="INVALID_FILE_TYPE",
            status=422,
            user_message="CSVファイルのみアップロード可能です",
            title="ファイル形式エラー"
        )

    # 処理...
    return {"status": "success"}
```

### 2. traceId の取得

```python
@router.post("/process")
async def process_data(request: Request):
    trace_id = getattr(request.state, "trace_id", None)

    # ログに traceId を記録
    logger.info(f"Processing started [traceId={trace_id}]")

    # 処理...
```

### 3. ジョブでのエラーハンドリング

```python
from backend_shared.src.domain import JobStatus, ProblemDetails
from datetime import datetime

async def process_async_job(job_id: str):
    try:
        # 処理...
        job_store[job_id].status = "completed"
        job_store[job_id].result = {"data": "..."}
    except Exception as e:
        # エラー時に ProblemDetails を保存
        error = ProblemDetails(
            status=500,
            code="PROCESSING_ERROR",
            userMessage=str(e),
            title="処理エラー",
            traceId=trace_id
        )

        job_store[job_id].status = "failed"
        job_store[job_id].error = error
        job_store[job_id].updatedAt = datetime.utcnow().isoformat()
```

## CORS設定

フロントエンドから `X-Request-ID` を読み取れるように `expose_headers` を設定します:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],  # 重要！
)
```

## テスト用エンドポイント

### POST /api/jobs/{job_id}/fail

ジョブを強制的に失敗させる（テスト用）

### POST /api/jobs/{job_id}/raise-error

DomainError を発生させる（エラーハンドラのテスト用）

## フロントエンドとの連携

### エラーレスポンスの処理

```typescript
import type { ProblemDetails } from "@/features/notification/model/contract";

try {
  const response = await fetch("/api/upload", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const problem: ProblemDetails = await response.json();
    console.error("Error:", problem.userMessage);
    console.error("TraceId:", problem.traceId);
  }
} catch (error) {
  console.error("Network error:", error);
}
```

### X-Request-ID の送信

```typescript
// リクエスト時に X-Request-ID を送信
const requestId = crypto.randomUUID();

const response = await fetch("/api/data", {
  headers: {
    "X-Request-ID": requestId,
  },
});

// レスポンスから X-Request-ID を取得
const responseRequestId = response.headers.get("X-Request-ID");
console.log("TraceId:", responseRequestId);
```

## ベストプラクティス

1. **明示的なエラーコード**: `code` は一意で分かりやすい名前を使用
2. **ユーザー向けメッセージ**: `userMessage` はエンドユーザーが理解できる内容に
3. **traceId の記録**: ログに必ず traceId を含める
4. **ジョブの適切な状態管理**: 失敗時は必ず `error` フィールドを設定

## 注意事項

- 本番環境では `allow_origins=["*"]` を適切なオリジンに変更すること
- ジョブストアは本番環境では Redis や DB を使用すること
- センシティブな情報を `userMessage` に含めないこと
- エラーログには詳細情報、ユーザーには要約のみ表示
