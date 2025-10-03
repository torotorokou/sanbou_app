import React from 'react';
import { Card, Table } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import type { CustomerData } from '../model/customer-dummy-data';

type Props = {
    title: string;
    data: CustomerData[];
    cardStyle?: React.CSSProperties;
    headStyle?: React.CSSProperties;
    style?: React.CSSProperties;
};

const customerColumns: ColumnsType<CustomerData> = [
    { title: '顧客名', dataIndex: 'name', key: 'name', width: 120 },
    {
        title: '合計重量(kg)',
        dataIndex: 'weight',
        key: 'weight',
        align: 'right' as const,
        width: 120,
    },
    {
        title: '合計金額(円)',
        dataIndex: 'amount',
        key: 'amount',
        align: 'right' as const,
        width: 120,
        render: (value: number) => value.toLocaleString(),
    },
    { title: '担当営業者', dataIndex: 'sales', key: 'sales', width: 120 },
];
const CustomerComparisonResultCard: React.FC<Props> = ({
    title,
    data,
    cardStyle,
    headStyle,
    style,
}) => (
    <Card
        title={title}
        style={{
            flex: 1,
            minHeight: 0,
            display: 'flex',
            flexDirection: 'column',
            ...style,
            ...cardStyle,
        }}
        headStyle={{ fontWeight: 600, ...headStyle }}
        bodyStyle={{ flex: 1, minHeight: 0, overflow: 'auto', padding: 0 }}
    >
    <div className="responsive-x" style={{ minHeight: 0 }}>
            <Table
                dataSource={data}
                columns={customerColumns}
                size='small'
                rowKey='key'
                pagination={false}
                locale={{ emptyText: '該当なし' }}
                scroll={{ x: 'max-content' }}
            />
        </div>
    </Card>
);

export default CustomerComparisonResultCard;
