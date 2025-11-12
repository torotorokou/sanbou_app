/**
 * External API Client
 * RAG、帳票、マニュアル、AI分類などの外部APIアクセス
 */

import { coreApi } from '@/shared';

// =============================
// RAG API
// =============================
export interface RAGAskRequest {
  query: string;
}

export interface RAGAskResponse {
  answer: string;
  sources?: Array<{
    title?: string;
    url?: string;
    excerpt?: string;
  }>;
}

/**
 * RAGに質問する
 */
export async function askRAG(query: string): Promise<RAGAskResponse> {
  return await coreApi.post<RAGAskResponse>('/core_api/external/rag/ask', { query });
}

// =============================
// Manual API
// =============================
export interface ManualSummary {
  id: string;
  title: string;
  category?: string;
  updated_at?: string;
}

export interface ManualDetail {
  id: string;
  title: string;
  content: string;
  sections?: Array<{
    id: string;
    title: string;
    content: string;
  }>;
}

/**
 * マニュアル一覧を取得
 */
export async function listManuals(): Promise<{ manuals: ManualSummary[] }> {
  return await coreApi.get<{ manuals: ManualSummary[] }>('/core_api/external/manual/list');
}

/**
 * 特定のマニュアルを取得
 */
export async function getManual(manualId: string): Promise<ManualDetail> {
  return await coreApi.get<ManualDetail>(`/core_api/external/manual/${manualId}`);
}

// =============================
// Ledger Report API
// =============================
export interface LedgerReportRequest {
  date: string;
  factory_id?: string;
  [key: string]: unknown;
}

export interface LedgerReportResponse {
  job_id?: string;
  status?: string;
  download_url?: string;
  [key: string]: unknown;
}

/**
 * 帳票生成リクエスト
 */
export async function generateLedgerReport(
  reportType: string,
  params: LedgerReportRequest
): Promise<LedgerReportResponse> {
  return await coreApi.post<LedgerReportResponse>(
    `/core_api/external/ledger/reports/${reportType}`,
    params
  );
}

// =============================
// AI Classification API
// =============================
export interface AIClassifyRequest {
  text: string;
}

export interface AIClassifyResponse {
  category: string;
  confidence?: number;
  [key: string]: unknown;
}

/**
 * テキスト分類
 */
export async function classifyText(text: string): Promise<AIClassifyResponse> {
  return await coreApi.post<AIClassifyResponse>('/core_api/external/ai/classify', { text });
}
