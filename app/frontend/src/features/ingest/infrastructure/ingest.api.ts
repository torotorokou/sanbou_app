/**
 * Ingest API Client
 * データ取込（CSV アップロード、予約登録）
 */

import { coreApi } from '@/shared';

export interface ReservationCreate {
  date: string; // YYYY-MM-DD
  trucks: number;
}

export interface ReservationResponse {
  date: string;
  trucks: number;
  created_at: string;
}

/**
 * CSV データをアップロード
 */
export async function uploadCSV(file: File): Promise<{ status: string; rows_inserted: number }> {
  const formData = new FormData();
  formData.append('file', file);
  
  return await coreApi.uploadForm<{ status: string; rows_inserted: number }>(
    '/core_api/ingest/csv',
    formData
  );
}

/**
 * トラック予約を作成
 */
export async function createReservation(
  request: ReservationCreate
): Promise<ReservationResponse> {
  return await coreApi.post<ReservationResponse>('/core_api/ingest/reserve', request);
}
