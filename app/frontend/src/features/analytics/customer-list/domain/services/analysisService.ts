import { useMemo } from 'react';
import type { CustomerData } from '../types';
import { allCustomerData } from '../types';

/**
 * Customer Churn Analysis ViewModel
 * 
 * 顧客離脱分析のためのViewModel
 * - currentCustomers: 今期（分析対象期間）の顧客
 * - previousCustomers: 前期（比較期間）の顧客
 * - lostCustomers: 離脱顧客（前期には存在したが今期には存在しない顧客）
 */
export interface CustomerChurnViewModel {
    /** 今期（分析対象期間）の顧客リスト */
    currentCustomers: CustomerData[];
    /** 前期（比較期間）の顧客リスト */
    previousCustomers: CustomerData[];
    /** 離脱顧客（前期 - 今期） */
    lostCustomers: CustomerData[];
}

/**
 * useCustomerComparison Hook (ViewModel)
 * 
 * 顧客の期間比較分析を行うViewModel Hook
 * 
 * @param currentMonths - 今期（分析対象期間）の月リスト (例: ['2024-05', '2024-06'])
 * @param previousMonths - 前期（比較期間）の月リスト (例: ['2024-03', '2024-04'])
 * @returns CustomerChurnViewModel - 分析結果
 */
export function useCustomerComparison(
    currentMonths: string[],
    previousMonths: string[]
): CustomerChurnViewModel {
    // 顧客集約ロジック（純粋関数として抽出可能）
    const aggregateCustomers = (months: string[]): CustomerData[] => {
        const map = new Map<string, CustomerData>();
        months.forEach((m) => {
            (allCustomerData[m] || []).forEach((c) => {
                if (!map.has(c.key)) {
                    map.set(c.key, { ...c });
                } else {
                    const exist = map.get(c.key)!;
                    exist.weight += c.weight;
                    exist.amount += c.amount;
                }
            });
        });
        return Array.from(map.values());
    };

    // 集計はuseMemoでキャッシュ
    const currentCustomers = useMemo(
        () => aggregateCustomers(currentMonths),
        [currentMonths]
    );
    const previousCustomers = useMemo(
        () => aggregateCustomers(previousMonths),
        [previousMonths]
    );
    
    // 離脱顧客: 前期には存在したが今期には存在しない顧客
    const lostCustomers = useMemo(
        () =>
            previousCustomers.filter(
                (c) => !currentCustomers.some((tc) => tc.key === c.key)
            ),
        [previousCustomers, currentCustomers]
    );

    return { currentCustomers, previousCustomers, lostCustomers };
}
