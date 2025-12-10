# Core API - BFF/Facade for Frontend

## Architecture

Core API is the **Backend-for-Frontend (BFF)** layer that acts as a single entry point for the frontend. It follows a clear separation of concerns:

- **Short-running sync calls**: Core API directly calls `rag_api`, `ledger_api`, `manual_api` via internal HTTP (1s timeout, no retry)
- **Long-running async jobs**: Core API queues jobs in `jobs.forecast_jobs` table → `forecast_worker` polls and executes → results stored in `forecast.predictions_daily`

### Technology Stack

- **FastAPI** with Pydantic v2 for validation
- **SQLAlchemy 2.x** (synchronous) with psycopg3
- **Alembic** for database migrations
- **PostgreSQL** with schema-based separation:
  - `core`: Ingest data (CSV, reservations)
  - `jobs`: Job queue table
  - `forecast`: Prediction results
- **httpx** for internal HTTP calls
- **Structured JSON logging** with python-json-logger

### Directory Structure

```
core_api/
├── app/
│   ├── app.py              # FastAPI application entry point
│   ├── deps.py             # Dependency injection (DI)
│   ├── routers/            # API endpoints (controllers)
│   │   ├── ingest.py       # CSV upload, reservations
│   │   ├── forecast.py     # Job creation, status, predictions
│   │   ├── kpi.py          # Dashboard queries
│   │   └── external.py     # Proxies to rag/ledger/manual
│   ├── services/           # Business logic (use cases)
│   │   ├── ingest_service.py
│   │   ├── forecast_service.py
│   │   └── kpi_service.py
│   ├── repositories/       # Data access layer
│   │   ├── orm_models.py   # SQLAlchemy ORM models
│   │   ├── core_repo.py
│   │   ├── job_repo.py
│   │   └── forecast_query_repo.py
│   ├── domain/             # DTOs and business rules
│   │   ├── models.py       # Pydantic DTOs
│   │   └── rules.py        # Business logic (holidays, etc.)
│   └── infra/              # Infrastructure layer
│       ├── db.py           # Database session
│       └── http.py         # HTTP client for internal APIs
├── migrations/             # Alembic migrations
│   ├── env.py
│   └── versions/
│       └── 001_initial_schema.py
├── alembic.ini
├── requirements.txt
├── Dockerfile
└── pyproject.toml
```

## API Endpoints

### Ingest (Command)

- `POST /api/ingest/csv` - Upload CSV data (multipart/form-data)
- `POST /api/ingest/reserve` - Create truck reservation

### Forecast (Job Queue)

- `POST /api/forecast/jobs` - Queue a forecast job
- `GET /api/forecast/jobs/{id}` - Get job status
- `GET /api/forecast/predictions?from=YYYY-MM-DD&to=YYYY-MM-DD` - Get predictions

### KPI (Query)

- `GET /api/kpi/overview` - Dashboard KPIs

### External (Sync Proxies)

- `POST /api/external/rag/ask` - RAG query (1s timeout)
- `GET /api/external/manual/list` - List manuals

### Health

- `GET /api/healthz` - Health check

## Database Schema

### jobs.forecast_jobs

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| job_type | TEXT | Job type (e.g., 'daily') |
| target_from | DATE | Start date |
| target_to | DATE | End date |
| status | TEXT | queued / running / done / failed |
| attempts | INT | Retry count |
| scheduled_for | TIMESTAMP | Scheduled execution time |
| actor | TEXT | User or system actor |
| payload_json | JSONB | Additional parameters |
| error_message | TEXT | Error details |
| created_at | TIMESTAMP | Created timestamp |
| updated_at | TIMESTAMP | Updated timestamp |

### forecast.predictions_daily

| Column | Type | Description |
|--------|------|-------------|
| date | DATE | Primary key |
| y_hat | NUMERIC | Predicted value |
| y_lo | NUMERIC | Lower bound |
| y_hi | NUMERIC | Upper bound |
| model_version | TEXT | Model version |
| generated_at | TIMESTAMP | Generation timestamp |

### core.inbound_actuals

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| date | DATE | Data date |
| data_json | JSONB | Flexible CSV data storage |
| created_at | TIMESTAMP | Created timestamp |

TODO: Define proper columns based on CSV spec.

### core.inbound_reservations

| Column | Type | Description |
|--------|------|-------------|
| date | DATE | Primary key |
| trucks | INT | Number of trucks |
| created_at | TIMESTAMP | Created timestamp |
| updated_at | TIMESTAMP | Updated timestamp |

## Development

### Prerequisites

- Docker & Docker Compose
- PostgreSQL 15+

### Setup

1. Set environment variables in `env/.env.local_dev`:

```bash
DATABASE_URL=postgresql://user:pass@db:5432/dbname
RAG_API_BASE=http://rag_api:8000
LEDGER_API_BASE=http://ledger_api:8000
MANUAL_API_BASE=http://manual_api:8000
```

2. Run database migrations:

```bash
docker-compose -f docker/docker-compose.dev.yml exec core_api alembic upgrade head
```

3. Start services:

```bash
docker-compose -f docker/docker-compose.dev.yml up -d
```

### Testing Endpoints

```bash
# Health check
curl http://localhost:8003/api/healthz

# Create a forecast job
curl -X POST http://localhost:8003/api/forecast/jobs \
  -H "Content-Type: application/json" \
  -d '{"target_from": "2025-01-01", "target_to": "2025-01-31"}'

# Check job status
curl http://localhost:8003/api/forecast/jobs/1

# Get predictions
curl "http://localhost:8003/api/forecast/predictions?from=2025-01-01&to=2025-01-31"
```

## Acceptance Criteria

✅ All endpoints are implemented with proper type hints and docstrings  
✅ `/healthz` returns 200 OK  
✅ `POST /forecast/jobs` returns `{id, status: 'queued'}`  
✅ `forecast_worker` picks up queued jobs and transitions status to `done/failed`  
✅ `GET /forecast/predictions` returns predictions within date range  
✅ Predictions are idempotent (UPSERT on date)  
✅ Internal HTTP calls (rag/ledger/manual) use 1s timeout, no retry  
✅ Database transactions are managed in Service layer  
✅ Structured JSON logging with important fields (job_id, status, error, actor, duration)  
✅ SQLAlchemy 2.x synchronous mode with psycopg3  

## TODO

- [ ] Define proper CSV column spec in `inbound_actuals`
- [ ] Implement authentication and populate `actor` field
- [ ] Add business day calculation in `domain/rules.py`
- [ ] Replace dummy predictor with real ML model
- [ ] Add retry logic for failed jobs (exponential backoff)
- [ ] Add monitoring and alerting for job failures
- [ ] Implement rate limiting for external API calls
- [ ] Add API versioning (e.g., `/api/v1/...`)

## Related Services

- **forecast_worker**: Background worker that executes forecast jobs
- **rag_api**: RAG query service
- **ledger_api**: Ledger and document generation
- **manual_api**: Manual/documentation service

## IAP (Identity-Aware Proxy) デバッグ

### 概要

GCP IAP 経由でのリクエストが FastAPI まで正しく到達し、IAP が付与するヘッダが適切に転送されているかを確認するためのデバッグエンドポイントを提供しています。

### エンドポイント

```
GET /core_api/debug/iap-headers
```

### IAP が付与する主要ヘッダ

- **X-Goog-Authenticated-User-Email**: ログインユーザーのメールアドレス  
  形式: `accounts.google.com:user@example.com`
  
- **X-Goog-Authenticated-User-Id**: ログインユーザーの内部 ID  
  形式: `accounts.google.com:123456789012345678901`
  
- **X-Goog-IAP-JWT-Assertion**: IAP が発行した JWT トークン（署名付き）

### テスト手順（PROD 環境）

1. **環境の準備**
   ```bash
   # PROD 環境で docker / nginx を起動・再起動
   cd /path/to/sanbou_app
   make prod-up   # または docker-compose -f docker/docker-compose.prod.yml up -d
   ```

2. **ブラウザからアクセス**
   ```
   https://<IAP付きのPRODドメイン>/core_api/debug/iap-headers
   ```

3. **IAP ログイン**
   - GCP IAP のログイン画面が表示されたら、許可された Google アカウントでログイン

4. **レスポンスの確認**
   
   以下のような JSON が返されることを確認:
   ```json
   {
     "x_goog_authenticated_user_email": "accounts.google.com:user@example.com",
     "x_goog_authenticated_user_id": "accounts.google.com:123456789012345678901",
     "x_goog_iap_jwt_assertion_exists": true,
     "x_goog_iap_jwt_assertion_preview": "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjBvZD...",
     "all_headers": {
       "host": "your-domain.com",
       "x-goog-authenticated-user-email": "accounts.google.com:user@example.com",
       ...
     }
   }
   ```

5. **確認項目**
   - ✅ `x_goog_authenticated_user_email` に正しいメールアドレスが含まれているか
   - ✅ `x_goog_authenticated_user_id` に ID が含まれているか
   - ✅ `x_goog_iap_jwt_assertion_exists` が `true` であるか
   - ✅ `all_headers` に IAP 関連ヘッダが含まれているか

### トラブルシューティング

#### ヘッダが `null` または存在しない場合

1. **Nginx 設定の確認**
   - `app/nginx/conf.d/prod.conf` が `_proxy_headers.conf` をインクルードしているか確認
   - `_proxy_headers.conf` に以下の設定があるか確認:
     ```nginx
     proxy_set_header X-Goog-Authenticated-User-Email $http_x_goog_authenticated_user_email;
     proxy_set_header X-Goog-Authenticated-User-Id $http_x_goog_authenticated_user_id;
     proxy_set_header X-Goog-IAP-JWT-Assertion $http_x_goog_iap_jwt_assertion;
     ```

2. **GCP Load Balancer + IAP の設定確認**
   - GCP コンソールで IAP が有効になっているか確認
   - バックエンドサービスに IAP が適用されているか確認
   - 使用している Google アカウントが IAP のアクセス許可リストに含まれているか確認

3. **ログの確認**
   ```bash
   # Core API のログを確認
   docker logs -f core_api
   
   # Nginx のログを確認
   docker logs -f nginx
   ```

### 次のステップ

このデバッグエンドポイントで IAP ヘッダが正しく受信できることを確認したら、次のステップに進みます:

1. **JWT 検証の実装**: `X-Goog-IAP-JWT-Assertion` の署名検証
2. **ユーザー情報の DB 連携**: `auth_users` テーブルとの紐付け
3. **認証ミドルウェアの統合**: 全エンドポイントでの自動認証
4. **デバッグエンドポイントの無効化**: 本番環境でのアクセス制限

### 注意事項

- このデバッグエンドポイントは **開発/検証用途** です
- `all_headers` には機密情報が含まれる可能性があります
- 本番環境では適切なアクセス制限を設けるか、無効化することを推奨します
- JWT の検証は行っていません（ヘッダの受信確認のみ）
