/**
 * Customer Comparison Sub-Feature
 *
 * 顧客比較（離脱分析）ロジック
 */

import type { CustomerData } from "../../shared/domain/types";

/**
 * 顧客比較結果
 */
export interface CustomerComparisonResult {
  /** 今期の顧客 */
  currentCustomers: CustomerData[];
  /** 前期の顧客 */
  previousCustomers: CustomerData[];
  /** 離脱顧客（前期には存在したが今期には存在しない） */
  lostCustomers: CustomerData[];
  /** 新規顧客（今期に新たに登場） */
  newCustomers: CustomerData[];
  /** 継続顧客（両期間に存在） */
  retainedCustomers: CustomerData[];
}
