/**
 * Inbound Daily API Client
 * 受入日次データの取得
 */

import { coreApi } from '@/shared';

export type CumScope = 'range' | 'month' | 'week' | 'none';

/**
 * 日次搬入量データ（カレンダー連続・0埋め済み）
 * バックエンドのInboundDailyRowと完全一致
 */
export interface InboundDailyRow {
  ddate: string; // 日付（YYYY-MM-DD形式）
  iso_year: number; // ISO年
  iso_week: number; // ISO週番号
  iso_dow: number; // ISO曜日（1=月, 7=日）
  is_business: boolean; // 営業日フラグ
  segment: string | null; // セグメント（オプション）
  ton: number; // 日次搬入量トン数
  cum_ton: number | null; // 累積搬入量トン数（cum_scope指定時のみ）
  prev_month_ton: number | null; // 先月（4週前）の同曜日の搬入量
  prev_year_ton: number | null; // 前年の同ISO週・同曜日の搬入量
  prev_month_cum_ton: number | null; // 先月の累積搬入量
  prev_year_cum_ton: number | null; // 前年の累積搬入量
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

  return await coreApi.get<InboundDailyRow[]>(`/core_api/inbound/daily?${queryParams.toString()}`);
}
