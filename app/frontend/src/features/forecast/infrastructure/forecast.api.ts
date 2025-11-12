/**
 * Forecast API Client
 * 予測ジョブの管理と予測結果の取得
 */

import { coreApi } from '@/shared';

export type JobType = 'daily_forecast' | 'weekly_forecast';
export type JobStatus = 'queued' | 'running' | 'completed' | 'failed';

export interface ForecastJobCreate {
  job_type: JobType;
  target_from: string; // YYYY-MM-DD
  target_to: string; // YYYY-MM-DD
  actor?: string;
  payload_json?: Record<string, unknown>;
}

export interface ForecastJobResponse {
  id: number;
  job_type: string;
  target_from: string;
  target_to: string;
  status: JobStatus;
  actor: string;
  payload_json?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  result_json?: Record<string, unknown> | null;
  error_message?: string | null;
}

export interface PredictionDTO {
  target_date: string;
  predicted_value: number;
  confidence_lower?: number | null;
  confidence_upper?: number | null;
}

/**
 * 予測ジョブを作成
 */
export async function createForecastJob(request: ForecastJobCreate): Promise<ForecastJobResponse> {
  return await coreApi.post<ForecastJobResponse>('/core_api/forecast/jobs', request);
}

/**
 * ジョブステータスを取得
 */
export async function getForecastJobStatus(jobId: number): Promise<ForecastJobResponse> {
  return await coreApi.get<ForecastJobResponse>(`/core_api/forecast/jobs/${jobId}`);
}

/**
 * 予測結果を取得
 */
export async function fetchPredictions(from: string, to: string): Promise<PredictionDTO[]> {
  return await coreApi.get<PredictionDTO[]>(
    `/core_api/forecast/predictions?from=${from}&to=${to}`
  );
}
