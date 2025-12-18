-- =====================================================================
-- 日次予測ジョブ投入SQL（target_date=2025-12-15）
-- 作成日: 2025-12-18
-- 目的: E2Eテスト用のジョブ投入
-- =====================================================================

-- ジョブ投入
INSERT INTO forecast.forecast_jobs (job_type, target_date, status, run_after)
VALUES ('daily_tplus1', DATE '2025-12-15', 'queued', CURRENT_TIMESTAMP)
RETURNING id, job_type, target_date, status, run_after, created_at;

-- 投入確認：直近5件のdaily_tplus1ジョブ
SELECT 
  id, 
  job_type, 
  target_date, 
  status, 
  attempt, 
  created_at, 
  started_at, 
  finished_at,
  LEFT(last_error, 200) AS last_error_preview
FROM forecast.forecast_jobs
WHERE job_type='daily_tplus1'
ORDER BY created_at DESC
LIMIT 5;
