"""
Forecast worker: polls jobs.forecast_jobs and executes predictions.
"""
import logging
import time
import os
from datetime import datetime
from pythonjsonlogger import jsonlogger
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from infra.db import SessionLocal
from domain.predictor import Predictor

# Structured JSON logging
logger = logging.getLogger("forecast_worker")
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter("%(asctime)s %(name)s %(levelname)s %(message)s")
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "3"))  # seconds


def claim_one_queued_job():
    """
    Claim one queued job using FOR UPDATE SKIP LOCKED.
    Returns (job_id, job_type, target_from, target_to) or None.
    """
    db = SessionLocal()
    try:
        sql = text("""
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
            RETURNING id, job_type, target_from, target_to
        """)
        result = db.execute(sql).fetchone()
        db.commit()
        return result
    except Exception as e:
        db.rollback()
        logger.error("Failed to claim job", extra={"error": str(e)})
        return None
    finally:
        db.close()


def mark_done(job_id: int):
    """Mark job as done."""
    db = SessionLocal()
    try:
        db.execute(
            text("UPDATE jobs.forecast_jobs SET status='done', updated_at=NOW() WHERE id=:id"),
            {"id": job_id}
        )
        db.commit()
    finally:
        db.close()


def mark_failed(job_id: int, error_message: str):
    """Mark job as failed with error message."""
    db = SessionLocal()
    try:
        db.execute(
            text("""
                UPDATE jobs.forecast_jobs
                SET status='failed', error_message=:error, updated_at=NOW()
                WHERE id=:id
            """),
            {"id": job_id, "error": error_message}
        )
        db.commit()
    finally:
        db.close()


def upsert_predictions(predictions: list):
    """
    UPSERT predictions into forecast.predictions_daily.
    Idempotent: if date exists, update values.
    """
    db = SessionLocal()
    try:
        for pred in predictions:
            stmt = text("""
                INSERT INTO forecast.predictions_daily (date, y_hat, y_lo, y_hi, model_version, generated_at)
                VALUES (:date, :y_hat, :y_lo, :y_hi, :model_version, NOW())
                ON CONFLICT (date) DO UPDATE SET
                    y_hat = EXCLUDED.y_hat,
                    y_lo = EXCLUDED.y_lo,
                    y_hi = EXCLUDED.y_hi,
                    model_version = EXCLUDED.model_version,
                    generated_at = NOW()
            """)
            db.execute(stmt, pred)
        db.commit()
    finally:
        db.close()


def execute_forecast_job(job_id: int, job_type: str, target_from, target_to):
    """
    Execute forecast job: run predictor and UPSERT results.
    """
    start = time.time()
    logger.info("Executing job", extra={"job_id": job_id, "job_type": job_type, "from": str(target_from), "to": str(target_to)})

    try:
        predictor = Predictor()
        predictions = predictor.predict(target_from, target_to)
        upsert_predictions(predictions)

        duration = time.time() - start
        logger.info("Job completed", extra={"job_id": job_id, "duration": duration, "rows": len(predictions)})
        mark_done(job_id)
    except Exception as e:
        duration = time.time() - start
        logger.error("Job failed", extra={"job_id": job_id, "error": str(e), "duration": duration})
        mark_failed(job_id, str(e))


def main():
    """Main worker loop."""
    logger.info("Forecast worker started", extra={"poll_interval": POLL_INTERVAL})

    while True:
        job = claim_one_queued_job()
        if job:
            job_id, job_type, target_from, target_to = job
            execute_forecast_job(job_id, job_type, target_from, target_to)
        else:
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
