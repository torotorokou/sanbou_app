/**
 * Inbound Daily API Client
 * 受入日次データの取得
 */

import { coreApi } from '@/shared';

export type CumScope = 'range' | 'month' | 'week' | 'none';

export interface InboundDailyRow {
  target_date: string;
  segment: string | null;
  ton: number;
  cum_ton: number | null;
}

export interface InboundDailyParams {
  start: string; // YYYY-MM-DD
  end: string; // YYYY-MM-DD
  segment?: string | null;
  cum_scope?: CumScope;
}

/**
 * 日次搬入量データを取得（カレンダー連続・0埋め済み）
 */
export async function fetchInboundDaily(params: InboundDailyParams): Promise<InboundDailyRow[]> {
  const { start, end, segment, cum_scope = 'none' } = params;
  
  const queryParams = new URLSearchParams({
    start,
    end,
    cum_scope,
  });
  
  if (segment) {
    queryParams.append('segment', segment);
  }
  
  return await coreApi.get<InboundDailyRow[]>(
    `/core_api/inbound/daily?${queryParams.toString()}`
  );
}
