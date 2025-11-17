-- job_repo__claim_job.sql
-- Claim an available forecast job for processing
--
-- Uses FOR UPDATE SKIP LOCKED to safely handle concurrent workers.
-- This query finds the first available queued job and atomically
-- updates its status to 'running', incrementing the attempt counter.
--
-- Returns:
--   id - The job ID that was claimed, or NULL if no jobs available

WITH picked AS (
    SELECT id FROM jobs.forecast_jobs
    WHERE status = 'queued'
      AND (scheduled_for IS NULL OR scheduled_for <= NOW())
    ORDER BY id
    FOR UPDATE SKIP LOCKED  -- ロック取得済みの行はスキップ(他ワーカーとの競合回避)
    LIMIT 1
)
UPDATE jobs.forecast_jobs
SET status = 'running',          -- 実行中に変更
    attempts = attempts + 1,     -- 実行回数をインクリメント
    updated_at = NOW()           -- 更新時刻を記録
WHERE id IN (SELECT id FROM picked)
RETURNING id
