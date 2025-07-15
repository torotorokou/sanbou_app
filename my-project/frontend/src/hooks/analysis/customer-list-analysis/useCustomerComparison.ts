import { useMemo } from 'react';
import type { CustomerData } from '@/data/analysis/customer-list-analysis/customer-dummy-data';
import { allCustomerData } from '@/data/analysis/customer-list-analysis/customer-dummy-data';

export function useCustomerComparison(
    targetMonths: string[],
    compareMonths: string[]
) {
    // 顧客集約ロジック
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
    const targetCustomers = useMemo(
        () => aggregateCustomers(targetMonths),
        [targetMonths]
    );
    const compareCustomers = useMemo(
        () => aggregateCustomers(compareMonths),
        [compareMonths]
    );
    const onlyCompare = useMemo(
        () =>
            compareCustomers.filter(
                (c) => !targetCustomers.some((tc) => tc.key === c.key)
            ),
        [compareCustomers, targetCustomers]
    );

    return { targetCustomers, compareCustomers, onlyCompare };
}
