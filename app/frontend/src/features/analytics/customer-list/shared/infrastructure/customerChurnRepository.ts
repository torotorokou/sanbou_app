/**
 * Customer Churn HTTP Repository
 *
 * CustomerChurnRepositoryの実装（HTTP経由でバックエンドAPIを呼び出し）
 */

import type { CustomerChurnRepository } from "../ports/customerChurnRepository";
import type {
  LostCustomer,
  CustomerChurnAnalyzeParams,
  SalesRep,
} from "../domain/types";
import { coreApi } from "@/shared";

/**
 * HTTP経由の顧客離脱分析Repository実装
 */
export class CustomerChurnHttpRepository implements CustomerChurnRepository {
  /**
   * 営業担当者リストを取得
   */
  async getSalesReps(): Promise<SalesRep[]> {
    const response = await coreApi.get<{
      sales_reps: Array<{
        rep_id: string;
        rep_name: string;
      }>;
    }>("/core_api/analysis/sales-reps");

    return response.sales_reps.map((rep) => ({
      salesRepId: rep.rep_id,
      salesRepName: rep.rep_name,
    }));
  }

  /**
   * 顧客離脱分析を実行
   *
   * @param params - 分析パラメータ
   * @returns 離脱顧客のリスト
   */
  async analyze(params: CustomerChurnAnalyzeParams): Promise<LostCustomer[]> {
    const response = await coreApi.post<{
      lost_customers: Array<{
        customer_id: string;
        customer_name: string;
        rep_id: string | null;
        rep_name: string | null;
        last_visit_date: string;
        prev_visit_days: number;
        prev_total_amount_yen: number;
        prev_total_qty_kg: number;
      }>;
    }>("/core_api/analysis/customer-churn/analyze", {
      current_start: params.currentStart,
      current_end: params.currentEnd,
      previous_start: params.previousStart,
      previous_end: params.previousEnd,
    });

    // APIレスポンスをドメイン型に変換（snake_case -> camelCase）
    return response.lost_customers.map((customer) => ({
      customerId: customer.customer_id,
      customerName: customer.customer_name,
      salesRepId: customer.rep_id,
      salesRepName: customer.rep_name,
      lastVisitDate: customer.last_visit_date,
      prevVisitDays: customer.prev_visit_days,
      prevTotalAmountYen: customer.prev_total_amount_yen,
      prevTotalQtyKg: customer.prev_total_qty_kg,
    }));
  }
}

/**
 * デフォルトのCustomerChurnRepositoryインスタンス
 */
export const customerChurnRepository = new CustomerChurnHttpRepository();
