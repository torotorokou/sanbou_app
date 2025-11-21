/**
 * Customer Comparison - Pure Functions
 * 
 * 顧客比較ロジックの純粋関数
 */

import type { CustomerData } from '../../shared/domain/types';

/**
 * 2つの顧客リストを比較し、片方にしか存在しない顧客を抽出する
 * 
 * @param sourceList - 元のリスト
 * @param excludeList - 除外するリスト
 * @returns sourceListには存在するが、excludeListには存在しない顧客
 */
export function getExclusiveCustomers(
    sourceList: CustomerData[],
    excludeList: CustomerData[]
): CustomerData[] {
    return sourceList.filter(
        (source) => !excludeList.some((exclude) => exclude.key === source.key)
    );
}

/**
 * 2つの顧客リストで共通する顧客を抽出する
 * 
 * @param list1 - リスト1
 * @param list2 - リスト2
 * @returns 両方に存在する顧客
 */
export function getCommonCustomers(
    list1: CustomerData[],
    list2: CustomerData[]
): CustomerData[] {
    return list1.filter(
        (customer1) => list2.some((customer2) => customer2.key === customer1.key)
    );
}
