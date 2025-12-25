/**
 * HttpInboundDailyRepository Implementation
 * 日次搬入量データ取得のHTTP実装
 */

import type {
  InboundDailyRepository,
  FetchDailyParams,
  InboundDailyRow,
} from '../ports/InboundDailyRepository';
import { DASHBOARD_ENDPOINTS } from '@/shared';

/**
 * HTTP経由で日次搬入量データを取得
 */
export class HttpInboundDailyRepository implements InboundDailyRepository {
  constructor(private readonly baseUrl: string = DASHBOARD_ENDPOINTS.inboundDaily) {}

  async fetchDaily(params: FetchDailyParams): Promise<InboundDailyRow[]> {
    const { start, end, segment, cum_scope = 'none' } = params;

    const url = new URL(this.baseUrl, window.location.origin);
    url.searchParams.set('start', start);
    url.searchParams.set('end', end);
    if (segment != null && segment !== '') {
      url.searchParams.set('segment', segment);
    }
    url.searchParams.set('cum_scope', cum_scope);

    const response = await fetch(url.toString());

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to fetch inbound daily: ${response.status} ${errorText}`);
    }

    const data: InboundDailyRow[] = await response.json();
    return data;
  }
}
