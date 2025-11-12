/**
 * KPI API Client
 * KPI概要データの取得
 */

import { coreApi } from '@/shared';

export interface KPIOverview {
  total_revenue: number;
  total_cost: number;
  profit_margin: number;
  customer_count: number;
  active_projects: number;
  // 他のKPI指標を追加可能
  [key: string]: unknown;
}

/**
 * KPI概要を取得
 */
export async function fetchKPIOverview(): Promise<KPIOverview> {
  return await coreApi.get<KPIOverview>('/core_api/kpi/overview');
}
