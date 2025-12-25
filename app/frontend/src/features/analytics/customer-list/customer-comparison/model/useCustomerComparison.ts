/**
 * Customer Comparison - ViewModel
 *
 * 顧客比較分析のViewModel
 */

import { useMemo } from "react";
import type { CustomerData } from "../../shared/domain/types";
import type { CustomerComparisonResult } from "../domain/types";
import { getExclusiveCustomers, getCommonCustomers } from "./comparison";

/**
 * 顧客比較分析のHook
 *
 * @param currentCustomers - 今期の顧客リスト
 * @param previousCustomers - 前期の顧客リスト
 * @returns 顧客比較結果
 */
export function useCustomerComparison(
  currentCustomers: CustomerData[],
  previousCustomers: CustomerData[],
): CustomerComparisonResult {
  // 離脱顧客: 前期には存在したが今期には存在しない
  const lostCustomers = useMemo(
    () => getExclusiveCustomers(previousCustomers, currentCustomers),
    [previousCustomers, currentCustomers],
  );

  // 新規顧客: 今期に新たに登場
  const newCustomers = useMemo(
    () => getExclusiveCustomers(currentCustomers, previousCustomers),
    [currentCustomers, previousCustomers],
  );

  // 継続顧客: 両期間に存在
  const retainedCustomers = useMemo(
    () => getCommonCustomers(currentCustomers, previousCustomers),
    [currentCustomers, previousCustomers],
  );

  return {
    currentCustomers,
    previousCustomers,
    lostCustomers,
    newCustomers,
    retainedCustomers,
  };
}
