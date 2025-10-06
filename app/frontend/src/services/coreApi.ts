/**
 * Core API Client - Frontend service for calling core_api (BFF).
 * All API calls should go through /api/** endpoints.
 */

const API_BASE = '/api';

interface RAGResponse {
  answer: string;
  sources?: string[];
}

interface ForecastJobResponse {
  id: number;
  status: 'queued' | 'running' | 'done' | 'failed';
  job_type: string;
  target_from: string;
  target_to: string;
  created_at: string;
  error_message?: string;
}

interface PredictionDTO {
  date: string;
  y_hat: number;
  y_lo?: number;
  y_hi?: number;
  model_version?: string;
  generated_at?: string;
}

interface ReservationResponse {
  date: string;
  trucks: number;
  created_at: string;
}

interface KPIOverview {
  total_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  latest_prediction_date?: string;
  last_updated: string;
}

/**
 * RAG API: Ask a question
 */
export async function askRag(query: string): Promise<RAGResponse> {
  const response = await fetch(`${API_BASE}/external/rag/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `RAG API error: ${response.status}`);
  }

  return response.json();
}

/**
 * Forecast: Create a new forecast job
 */
export async function createForecastJob(
  from: string,
  to: string,
  jobType: string = 'daily'
): Promise<ForecastJobResponse> {
  const response = await fetch(`${API_BASE}/forecast/jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      target_from: from,
      target_to: to,
      job_type: jobType,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `Forecast job creation failed: ${response.status}`);
  }

  return response.json();
}

/**
 * Forecast: Get job status
 */
export async function getForecastJobStatus(jobId: number): Promise<ForecastJobResponse> {
  const response = await fetch(`${API_BASE}/forecast/jobs/${jobId}`);

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Job not found');
    }
    throw new Error(`Failed to get job status: ${response.status}`);
  }

  return response.json();
}

/**
 * Forecast: Get predictions for date range
 */
export async function getForecastPredictions(
  from: string,
  to: string
): Promise<PredictionDTO[]> {
  const params = new URLSearchParams({ from, to });
  const response = await fetch(`${API_BASE}/forecast/predictions?${params}`);

  if (!response.ok) {
    throw new Error(`Failed to get predictions: ${response.status}`);
  }

  return response.json();
}

/**
 * Ingest: Create truck reservation
 */
export async function createReservation(
  date: string,
  trucks: number
): Promise<ReservationResponse> {
  const response = await fetch(`${API_BASE}/ingest/reserve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ date, trucks }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `Reservation failed: ${response.status}`);
  }

  return response.json();
}

/**
 * Ingest: Upload CSV file
 */
export async function uploadCSV(file: File): Promise<{ status: string; rows_inserted: number }> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/ingest/csv`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `CSV upload failed: ${response.status}`);
  }

  return response.json();
}

/**
 * KPI: Get dashboard overview
 */
export async function getKPIOverview(): Promise<KPIOverview> {
  const response = await fetch(`${API_BASE}/kpi/overview`);

  if (!response.ok) {
    throw new Error(`Failed to get KPI overview: ${response.status}`);
  }

  return response.json();
}

/**
 * Manual: List all manuals
 */
export async function listManuals(): Promise<any[]> {
  const response = await fetch(`${API_BASE}/external/manual/list`);

  if (!response.ok) {
    throw new Error(`Failed to list manuals: ${response.status}`);
  }

  const data = await response.json();
  return data.manuals || [];
}

/**
 * Health check
 */
export async function checkHealth(): Promise<{ status: string; service: string }> {
  const response = await fetch(`${API_BASE}/healthz`);

  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }

  return response.json();
}
