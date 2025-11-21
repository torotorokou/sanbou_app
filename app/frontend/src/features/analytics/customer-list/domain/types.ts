// /app/src/data/analysis/customer-list-analysis/customer-dummy-data.ts

export type CustomerData = {
    key: string;
    name: string;
    weight: number;
    amount: number;
    sales: string;
    lastDeliveryDate?: string; // 最終搬入日 (YYYY-MM-DD形式)
};

export const allCustomerData: { [month: string]: CustomerData[] } = {
    '2024-04': [
        {
            key: 'C001',
            name: '顧客A',
            weight: 1320,
            amount: 38000,
            sales: '田中',
        },
        {
            key: 'C002',
            name: '顧客B',
            weight: 950,
            amount: 29000,
            sales: '佐藤',
        },
        {
            key: 'C003',
            name: '顧客C',
            weight: 680,
            amount: 19000,
            sales: '田中',
        },
        {
            key: 'C010',
            name: '顧客J',
            weight: 420,
            amount: 13000,
            sales: '高橋',
        },
    ],
    // ...（省略。以前のまま全月分貼ってください）...
    '2024-05': [
        {
            key: 'C001',
            name: '顧客A',
            weight: 880,
            amount: 27000,
            sales: '田中',
        },
        {
            key: 'C002',
            name: '顧客B',
            weight: 1110,
            amount: 35500,
            sales: '佐藤',
        },
        {
            key: 'C003',
            name: '顧客C',
            weight: 640,
            amount: 18500,
            sales: '田中',
        },
        {
            key: 'C004',
            name: '顧客D',
            weight: 330,
            amount: 8000,
            sales: '鈴木',
        },
        {
            key: 'C011',
            name: '顧客K',
            weight: 150,
            amount: 4500,
            sales: '山田',
        },
    ],
    // ...（以下同様に省略）...
    '2024-06': [
        {
            key: 'C001',
            name: '顧客A',
            weight: 1200,
            amount: 40000,
            sales: '田中',
        },
        {
            key: 'C003',
            name: '顧客C',
            weight: 740,
            amount: 20500,
            sales: '田中',
        },
        {
            key: 'C004',
            name: '顧客D',
            weight: 580,
            amount: 17500,
            sales: '鈴木',
        },
        {
            key: 'C005',
            name: '顧客E',
            weight: 100,
            amount: 3000,
            sales: '高橋',
        },
        { key: 'C012', name: '顧客L', weight: 90, amount: 2000, sales: '山田' },
    ],
    '2024-07': [
        {
            key: 'C001',
            name: '顧客A',
            weight: 990,
            amount: 33500,
            sales: '田中',
        },
        {
            key: 'C002',
            name: '顧客B',
            weight: 1400,
            amount: 40000,
            sales: '佐藤',
        },
        {
            key: 'C005',
            name: '顧客E',
            weight: 370,
            amount: 11500,
            sales: '高橋',
        },
        {
            key: 'C006',
            name: '顧客F',
            weight: 700,
            amount: 23000,
            sales: '鈴木',
        },
        {
            key: 'C013',
            name: '顧客M',
            weight: 230,
            amount: 8000,
            sales: '山田',
        },
    ],
    '2024-08': [
        {
            key: 'C001',
            name: '顧客A',
            weight: 1700,
            amount: 59000,
            sales: '田中',
        },
        {
            key: 'C002',
            name: '顧客B',
            weight: 600,
            amount: 18800,
            sales: '佐藤',
        },
        {
            key: 'C003',
            name: '顧客C',
            weight: 900,
            amount: 26500,
            sales: '田中',
        },
        {
            key: 'C007',
            name: '顧客G',
            weight: 310,
            amount: 9500,
            sales: '鈴木',
        },
        {
            key: 'C014',
            name: '顧客N',
            weight: 210,
            amount: 6000,
            sales: '山田',
        },
    ],
    '2024-09': [
        {
            key: 'C002',
            name: '顧客B',
            weight: 830,
            amount: 25100,
            sales: '佐藤',
        },
        {
            key: 'C003',
            name: '顧客C',
            weight: 1150,
            amount: 32500,
            sales: '田中',
        },
        {
            key: 'C005',
            name: '顧客E',
            weight: 660,
            amount: 21000,
            sales: '高橋',
        },
        {
            key: 'C008',
            name: '顧客H',
            weight: 120,
            amount: 3500,
            sales: '鈴木',
        },
        {
            key: 'C015',
            name: '顧客O',
            weight: 250,
            amount: 9000,
            sales: '山田',
        },
    ],
};
