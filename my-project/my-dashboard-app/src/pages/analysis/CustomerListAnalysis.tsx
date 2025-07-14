import React, { useState } from 'react';
import {
    Row,
    Col,
    Typography,
    DatePicker,
    Button,
    Modal,
    Spin,
    Card,
    Table,
} from 'antd';
import dayjs, { Dayjs } from 'dayjs';
const { Title } = Typography;

type CustomerData = {
    key: string;
    name: string;
    weight: number;
    amount: number;
    sales: string;
};

function getMonthRange(start: Dayjs | null, end: Dayjs | null): string[] {
    if (!start || !end) return [];
    const range: string[] = [];
    let current = start.startOf('month');
    while (
        current.isBefore(end.endOf('month')) ||
        current.isSame(end, 'month')
    ) {
        range.push(current.format('YYYY-MM'));
        current = current.add(1, 'month');
        if (range.length > 24) break;
    }
    return range;
}

const allCustomerData: { [month: string]: CustomerData[] } = {
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

const customerColumns = [
    { title: '顧客名', dataIndex: 'name', key: 'name', width: 120 },
    {
        title: '合計重量(kg)',
        dataIndex: 'weight',
        key: 'weight',
        align: 'right',
        width: 120,
    },
    {
        title: '合計金額(円)',
        dataIndex: 'amount',
        key: 'amount',
        align: 'right',
        width: 120,
        render: (value: number) => value.toLocaleString(),
    },
    { title: '担当営業者', dataIndex: 'sales', key: 'sales', width: 120 },
];

function aggregateCustomers(months: string[]): CustomerData[] {
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
}

const CustomerListAnalysis: React.FC = () => {
    const [targetStart, setTargetStart] = useState<Dayjs | null>(null);
    const [targetEnd, setTargetEnd] = useState<Dayjs | null>(null);
    const [compareStart, setCompareStart] = useState<Dayjs | null>(null);
    const [compareEnd, setCompareEnd] = useState<Dayjs | null>(null);

    const [analysisStarted, setAnalysisStarted] = useState(false);
    const [isAnalyzing, setIsAnalyzing] = useState(false);

    const targetMonths = getMonthRange(targetStart, targetEnd);
    const compareMonths = getMonthRange(compareStart, compareEnd);

    const targetCustomers = aggregateCustomers(targetMonths);
    const compareCustomers = aggregateCustomers(compareMonths);

    const onlyCompare = compareCustomers.filter(
        (c) => !targetCustomers.some((tc) => tc.key === c.key)
    );

    const handleAnalyze = () => {
        setIsAnalyzing(true);
        setAnalysisStarted(false);
        setTimeout(() => {
            setIsAnalyzing(false);
            setAnalysisStarted(true);
        }, 1000);
    };

    const isButtonDisabled =
        !targetStart ||
        !targetEnd ||
        !compareStart ||
        !compareEnd ||
        targetEnd.isBefore(targetStart, 'month') ||
        compareEnd.isBefore(compareStart, 'month') ||
        isAnalyzing;

    return (
        <div style={{ height: '100vh', minHeight: 0 }}>
            {/* 分析中モーダル */}
            <Modal
                open={isAnalyzing}
                footer={null}
                closable={false}
                maskClosable={false}
                centered
                zIndex={3000}
                bodyStyle={{ textAlign: 'center', padding: '48px 24px' }}
            >
                <Spin size='large' style={{ marginBottom: 16 }} />
                <div style={{ fontWeight: 600, fontSize: 18, marginTop: 12 }}>
                    分析中です…
                </div>
                <div style={{ color: '#888', marginTop: 8 }}>
                    データを比較しています。しばらくお待ちください。
                </div>
            </Modal>
            <Row gutter={24} style={{ height: '100%', minHeight: 0 }}>
                {/* 左カラム（高さ詰める） */}
                <Col
                    span={7}
                    style={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 12,
                        height: 'auto',
                    }}
                >
                    <Card
                        title='比較条件の選択'
                        bordered={false}
                        style={{
                            boxShadow: '0 2px 8px rgba(0,0,0,0.07)',
                        }}
                        headStyle={{ background: '#f0f5ff', fontWeight: 600 }}
                    >
                        <Title level={5} style={{ marginBottom: 12 }}>
                            対象月グループ
                        </Title>
                        <div style={{ marginBottom: 8 }}>
                            開始月:{' '}
                            <DatePicker
                                picker='month'
                                value={targetStart}
                                onChange={setTargetStart}
                                style={{ width: 120 }}
                            />
                            <span style={{ margin: '0 8px' }}>～</span>
                            終了月:{' '}
                            <DatePicker
                                picker='month'
                                value={targetEnd}
                                onChange={setTargetEnd}
                                style={{ width: 120 }}
                            />
                        </div>
                        <Title level={5} style={{ margin: '24px 0 8px 0' }}>
                            比較月グループ
                        </Title>
                        <div style={{ marginBottom: 8 }}>
                            開始月:{' '}
                            <DatePicker
                                picker='month'
                                value={compareStart}
                                onChange={setCompareStart}
                                style={{ width: 120 }}
                            />
                            <span style={{ margin: '0 8px' }}>～</span>
                            終了月:{' '}
                            <DatePicker
                                picker='month'
                                value={compareEnd}
                                onChange={setCompareEnd}
                                style={{ width: 120 }}
                            />
                        </div>
                    </Card>

                    <Button
                        type='primary'
                        size='large'
                        block
                        disabled={isButtonDisabled}
                        onClick={handleAnalyze}
                        style={{ fontWeight: 600, letterSpacing: 1 }}
                    >
                        分析する
                    </Button>
                </Col>
                {/* 右カラム（縦いっぱい3分割） */}
                <Col
                    span={17}
                    style={{
                        height: '100%',
                        minHeight: 0,
                        display: 'flex',
                        flexDirection: 'column',
                    }}
                >
                    {!analysisStarted ? (
                        <Card
                            style={{
                                marginTop: 24,
                                color: '#888',
                                height: '100%',
                                minHeight: 0,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                            }}
                        >
                            左で月を選択し、「分析する」ボタンを押してください。
                        </Card>
                    ) : (
                        <div
                            style={{
                                display: 'flex',
                                flexDirection: 'column',
                                gap: 12,
                                height: '100%',
                                minHeight: 0,
                                flex: 1,
                            }}
                        >
                            <Card
                                title='比較月グループにしかいない顧客'
                                style={{
                                    flex: 4,
                                    minHeight: 0,
                                    display: 'flex',
                                    flexDirection: 'column',
                                }}
                                headStyle={{
                                    background: '#e6f7ff',
                                    fontWeight: 600,
                                }}
                                bodyStyle={{
                                    flex: 1,
                                    minHeight: 0,
                                    overflow: 'auto',
                                    padding: 0,
                                }}
                            >
                                <Table
                                    dataSource={onlyCompare}
                                    columns={customerColumns}
                                    size='small'
                                    rowKey='key'
                                    pagination={false}
                                    locale={{ emptyText: '該当なし' }}
                                    scroll={{ y: true }}
                                    style={{ minHeight: 0 }}
                                />
                            </Card>
                            <Card
                                title='対象月グループの顧客'
                                style={{
                                    flex: 3,
                                    minHeight: 0,
                                    display: 'flex',
                                    flexDirection: 'column',
                                }}
                                headStyle={{
                                    background: '#f5faff',
                                    fontWeight: 600,
                                }}
                                bodyStyle={{
                                    flex: 1,
                                    minHeight: 0,
                                    overflow: 'auto',
                                    padding: 0,
                                }}
                            >
                                <Table
                                    dataSource={targetCustomers}
                                    columns={customerColumns}
                                    size='small'
                                    rowKey='key'
                                    pagination={false}
                                    locale={{ emptyText: '該当なし' }}
                                    scroll={{ y: true }}
                                    style={{ minHeight: 0 }}
                                />
                            </Card>
                            <Card
                                title='比較月グループの顧客'
                                style={{
                                    flex: 3,
                                    minHeight: 0,
                                    display: 'flex',
                                    flexDirection: 'column',
                                }}
                                headStyle={{
                                    background: '#f5faff',
                                    fontWeight: 600,
                                }}
                                bodyStyle={{
                                    flex: 1,
                                    minHeight: 0,
                                    overflow: 'auto',
                                    padding: 0,
                                }}
                            >
                                <Table
                                    dataSource={compareCustomers}
                                    columns={customerColumns}
                                    size='small'
                                    rowKey='key'
                                    pagination={false}
                                    locale={{ emptyText: '該当なし' }}
                                    scroll={{ y: true }}
                                    style={{ minHeight: 0 }}
                                />
                            </Card>
                        </div>
                    )}
                </Col>
            </Row>
        </div>
    );
};

export default CustomerListAnalysis;
