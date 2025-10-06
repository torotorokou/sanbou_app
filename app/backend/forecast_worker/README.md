# Forecast Worker

## Overview

Background worker that polls `jobs.forecast_jobs` table and executes forecast predictions. Results are stored in `forecast.predictions_daily` with UPSERT semantics (idempotent).

## Architecture

- **No HTTP server**: Worker is a long-running Python process that polls the database
- **Job claiming**: Uses `FOR UPDATE SKIP LOCKED` to atomically claim jobs from multiple worker instances
- **Idempotent execution**: UPSERT predictions to avoid duplicates on retry
- **Error handling**: Failed jobs are marked with status='failed' and error message

## Technology

- **SQLAlchemy 2.x** (synchronous) with psycopg3
- **Structured JSON logging**
- **Minimal dependencies** (no FastAPI, no HTTP)

## Directory Structure

```
forecast_worker/
├── app/
│   └── worker.py           # Main worker loop
├── infra/
│   └── db.py               # Database connection
├── domain/
│   └── predictor.py        # Prediction logic (dummy for now)
├── requirements.txt
├── Dockerfile
└── pyproject.toml
```

## Worker Logic

1. **Poll**: Every 3 seconds, query `jobs.forecast_jobs` for `status='queued'` jobs
2. **Claim**: Atomically claim one job using `FOR UPDATE SKIP LOCKED`
3. **Execute**: Run predictor for the date range
4. **UPSERT**: Insert/update predictions in `forecast.predictions_daily`
5. **Update**: Mark job as `done` or `failed`

## Database Queries

### Claim Job (Atomic)

```sql
WITH picked AS (
    SELECT id, job_type, target_from, target_to
    FROM jobs.forecast_jobs
    WHERE status = 'queued'
      AND (scheduled_for IS NULL OR scheduled_for <= NOW())
    ORDER BY id
    FOR UPDATE SKIP LOCKED
    LIMIT 1
)
UPDATE jobs.forecast_jobs
SET status = 'running', attempts = attempts + 1, updated_at = NOW()
WHERE id IN (SELECT id FROM picked)
RETURNING id, job_type, target_from, target_to;
```

### UPSERT Predictions

```sql
INSERT INTO forecast.predictions_daily (date, y_hat, y_lo, y_hi, model_version, generated_at)
VALUES (:date, :y_hat, :y_lo, :y_hi, :model_version, NOW())
ON CONFLICT (date) DO UPDATE SET
    y_hat = EXCLUDED.y_hat,
    y_lo = EXCLUDED.y_lo,
    y_hi = EXCLUDED.y_hi,
    model_version = EXCLUDED.model_version,
    generated_at = NOW();
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/db` |
| `POLL_INTERVAL` | Polling interval in seconds | `3` |
| `SQL_ECHO` | Enable SQLAlchemy query logging | `false` |

## Development

### Local Testing

```bash
# Set environment
export DATABASE_URL=postgresql://user:pass@localhost:5432/db

# Run worker
python app/worker.py
```

### Docker

```bash
docker-compose -f docker/docker-compose.dev.yml up forecast_worker
```

## Logging

Worker uses structured JSON logging with the following fields:

- `job_id`: Job ID being processed
- `job_type`: Type of job
- `from`, `to`: Date range
- `duration`: Execution time in seconds
- `rows`: Number of predictions generated
- `error`: Error message (if failed)

Example log:

```json
{
  "asctime": "2025-10-06 12:34:56",
  "name": "forecast_worker",
  "levelname": "INFO",
  "message": "Job completed",
  "job_id": 123,
  "duration": 2.5,
  "rows": 31
}
```

## Scaling

- **Horizontal scaling**: Run multiple worker instances. `FOR UPDATE SKIP LOCKED` ensures no job is claimed twice.
- **Vertical scaling**: Increase CPU/memory for faster predictions.

## TODO

- [ ] Replace dummy predictor with real ML model (Prophet, etc.)
- [ ] Add retry logic with exponential backoff for transient failures
- [ ] Add metrics (Prometheus) for monitoring
- [ ] Add health check endpoint (optional HTTP server)
- [ ] Implement scheduled jobs (e.g., daily at 2am)
- [ ] Add job priority field for queue ordering

## Troubleshooting

### Worker not picking up jobs

1. Check database connectivity: `psql $DATABASE_URL`
2. Verify job status: `SELECT * FROM jobs.forecast_jobs WHERE status='queued';`
3. Check worker logs for errors

### Jobs stuck in 'running' status

- Worker crashed before completing job
- Solution: Reset status manually or implement timeout mechanism

```sql
UPDATE jobs.forecast_jobs
SET status = 'queued', updated_at = NOW()
WHERE status = 'running' AND updated_at < NOW() - INTERVAL '1 hour';
```

### Duplicate predictions

- Should not happen (UPSERT is idempotent)
- If it occurs, check `forecast.predictions_daily` for primary key violations
