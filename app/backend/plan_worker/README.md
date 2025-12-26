# Plan Worker

## Overview

Simple background worker template for executing plan-related tasks.

## Architecture

- **No HTTP server**: Worker is a long-running Python process
- **Minimal dependencies**: Pure Python implementation
- **Extensible**: Easy to add custom business logic

## Technology

- **Python 3.12**
- **Minimal dependencies** (add as needed)

## Directory Structure

```
plan_worker/
├── app/
│   └── worker.py           # Main worker loop
├── infra/
│   └── db.py               # Infrastructure (database, etc.)
├── domain/
│   └── predictor.py        # Business logic
├── requirements.txt        # Dependencies
├── Dockerfile              # Container definition
└── pyproject.toml          # Package metadata
```

## Worker Logic

1. **Poll**: Check for tasks periodically
2. **Process**: Execute business logic
3. **Loop**: Continue indefinitely

## Environment Variables

| Variable        | Description                 | Default |
| --------------- | --------------------------- | ------- |
| `POLL_INTERVAL` | Polling interval in seconds | `10`    |

## Development

### Local Testing

```bash
# Run worker
python app/worker.py
```

### Docker

```bash
# Build
docker build -t plan_worker -f plan_worker/Dockerfile --build-arg BUILDKIT_INLINE_CACHE=1 .

# Run
docker run --rm plan_worker
```

## TODO

- [ ] Add database connection logic
- [ ] Implement actual business logic
- [ ] Add error handling and retry logic
- [ ] Add monitoring and metrics
- [ ] Add unit tests

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
