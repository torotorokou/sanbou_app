# Core API Migration - Quick Start Guide

## 🎯 What Was Done

Successfully migrated `sql_api` → `core_api` as a **BFF (Backend-for-Frontend)** with:

- ✅ Clean Architecture (Router → Service → Repository)
- ✅ Job Queue System for long-running tasks
- ✅ Background Worker for async processing
- ✅ Multi-schema database (core / jobs / forecast)
- ✅ Alembic migrations
- ✅ 3-tier network isolation (prod)
- ✅ Structured JSON logging
- ✅ Health checks for all services
- ✅ Acceptance test suite

## 🚀 Quick Start

### 1. Start Development Environment

```bash
cd /home/koujiro/work_env/22.Work_React/sanbou_app

# Start all services
docker-compose -f docker/docker-compose.dev.yml up -d

# Run database migrations
docker-compose -f docker/docker-compose.dev.yml exec core_api alembic upgrade head

# View logs
docker-compose -f docker/docker-compose.dev.yml logs -f core_api forecast_worker
```

### 2. Test the API

```bash
# Run acceptance tests
./scripts/test_acceptance.sh

# Or test manually:
curl http://localhost:8003/api/healthz
curl -X POST http://localhost:8003/api/forecast/jobs \
  -H "Content-Type: application/json" \
  -d '{"target_from": "2025-01-01", "target_to": "2025-01-31"}'
```

### 3. Access Services

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | React app (Vite dev server) |
| Core API | http://localhost:8003 | BFF (all /api/** requests) |
| API Docs | http://localhost:8003/docs | Swagger UI |

## 📁 Key Files

```
app/backend/
├── core_api/                    # Main BFF API
│   ├── app/app.py              # FastAPI entry point
│   ├── app/routers/            # API endpoints
│   ├── app/services/           # Business logic
│   ├── app/repositories/       # Data access
│   ├── migrations/             # Alembic migrations
│   └── README.md               # Detailed docs
│
├── forecast_worker/             # Background job processor
│   ├── app/worker.py           # Main worker loop
│   ├── domain/predictor.py     # Prediction logic (dummy)
│   └── README.md               # Worker docs
│
docker/
├── docker-compose.dev.yml      # Development config
└── docker-compose.prod.yml     # Production config (3-tier network)

docs/
└── CORE_API_IMPLEMENTATION.md  # Complete implementation report

scripts/
├── test_acceptance.sh          # Automated acceptance tests
└── db_permissions.sql          # Database role setup
```

## 🔧 Environment Variables

Add to `env/.env.local_dev`:

```bash
# Core API
DATABASE_URL=postgresql://user:pass@db:5432/dbname
RAG_API_BASE=http://rag_api:8000
LEDGER_API_BASE=http://ledger_api:8000
MANUAL_API_BASE=http://manual_api:8000

# Forecast Worker
POLL_INTERVAL=3
```

## 📊 API Endpoints

### Job Queue (Async)

```bash
# Create job
POST /api/forecast/jobs
{
  "target_from": "2025-01-01",
  "target_to": "2025-01-31"
}
→ Returns: {"id": 1, "status": "queued"}

# Check status
GET /api/forecast/jobs/1
→ Returns: {"id": 1, "status": "done", ...}

# Get predictions
GET /api/forecast/predictions?from=2025-01-01&to=2025-01-31
→ Returns: [{"date": "2025-01-01", "y_hat": 100.5, ...}, ...]
```

### Ingest (Command)

```bash
# Upload CSV
POST /api/ingest/csv
(multipart/form-data)

# Create reservation
POST /api/ingest/reserve
{
  "date": "2025-01-15",
  "trucks": 5
}
```

### KPI (Query)

```bash
# Dashboard overview
GET /api/kpi/overview
→ Returns: {"total_jobs": 10, "completed_jobs": 8, ...}
```

### External (Sync Proxies)

```bash
# RAG query (1s timeout)
POST /api/external/rag/ask
{
  "query": "検索クエリ"
}

# List manuals
GET /api/external/manual/list
```

## 🏗️ Architecture

```
Frontend (/api/**) 
    ↓
Core API (BFF)
    ├─→ Internal HTTP (sync) → rag_api / ledger_api / manual_api
    └─→ DB Write → jobs.forecast_jobs (queued)
                      ↓
                Forecast Worker (poll)
                      ↓
                Execute & UPSERT → forecast.predictions_daily
```

## 🔐 Database Schemas

- **core**: Ingest data (actuals, reservations)
- **jobs**: Job queue (forecast_jobs)
- **forecast**: Prediction results (predictions_daily)

## 📝 TODO

- [ ] Define proper CSV schema (inbound_actuals)
- [ ] Replace dummy predictor with real ML model
- [ ] Implement authentication (populate actor field)
- [ ] Add business day calculation
- [ ] Migrate frontend to use /api/** exclusively

## 📚 Documentation

- [Core API README](app/backend/core_api/README.md) - API details
- [Forecast Worker README](app/backend/forecast_worker/README.md) - Worker details
- [Implementation Report](docs/CORE_API_IMPLEMENTATION.md) - Complete report

## 🆘 Troubleshooting

### Worker not picking up jobs

```bash
# Check worker logs
docker-compose -f docker/docker-compose.dev.yml logs forecast_worker

# Check database
docker-compose -f docker/docker-compose.dev.yml exec db psql -U user -d dbname
SELECT * FROM jobs.forecast_jobs WHERE status='queued';
```

### Migrations fail

```bash
# Reset database (dev only!)
docker-compose -f docker/docker-compose.dev.yml down -v
docker-compose -f docker/docker-compose.dev.yml up -d db
docker-compose -f docker/docker-compose.dev.yml exec core_api alembic upgrade head
```

### API not responding

```bash
# Check health
curl http://localhost:8003/api/healthz

# Check logs
docker-compose -f docker/docker-compose.dev.yml logs core_api
```

## ✅ Acceptance Criteria (All Met)

- ✅ /healthz returns 200 OK
- ✅ POST /forecast/jobs returns {id, status: 'queued'}
- ✅ Worker processes jobs (queued → running → done/failed)
- ✅ GET /forecast/predictions returns results
- ✅ Predictions are idempotent (UPSERT)
- ✅ Internal HTTP calls use 1s timeout, no retry
- ✅ Structured JSON logging
- ✅ SQLAlchemy 2.x with psycopg3
- ✅ All code has type hints and docstrings

## 🎉 Status

**COMPLETE** - Ready for testing and integration!

**Date**: 2025-10-06
