/**
 * Customer Aggregation Sub-Feature
 * 
 * 顧客データの集約ロジック
 */

import type { CustomerData } from '../../domain/types';

/**
 * 複数月の顧客データを集約する
 * 
 * @param months - 月リスト (例: ['2024-01', '2024-02'])
 * @param dataSource - 月ごとの顧客データソース
 * @returns 集約された顧客データ
 */
export function aggregateCustomers(
    months: string[],
    dataSource: Record<string, CustomerData[]>
): CustomerData[] {
    const map = new Map<string, CustomerData>();
    
    months.forEach((month) => {
        const monthlyData = dataSource[month] || [];
        
        monthlyData.forEach((customer) => {
            if (!map.has(customer.key)) {
                map.set(customer.key, { ...customer });
            } else {
                const existing = map.get(customer.key)!;
                existing.weight += customer.weight;
                existing.amount += customer.amount;
            }
        });
    });
    
    return Array.from(map.values());
}
