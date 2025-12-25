import React from 'react';
import { Card, Table } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import type { CustomerData } from '../../shared/domain/types';

type Props = {
  title: string;
  data: CustomerData[];
  cardStyle?: React.CSSProperties;
  headerStyle?: React.CSSProperties;
  style?: React.CSSProperties;
};

const customerColumns: ColumnsType<CustomerData> = [
  {
    title: '顧客CD',
    dataIndex: 'key',
    key: 'key',
    width: 100,
    sorter: (a, b) => a.key.localeCompare(b.key),
  },
  {
    title: '顧客名',
    dataIndex: 'name',
    key: 'name',
    width: 200,
    sorter: (a, b) => a.name.localeCompare(b.name),
  },
  {
    title: '合計重量(kg)',
    dataIndex: 'weight',
    key: 'weight',
    align: 'right' as const,
    width: 140,
    sorter: (a, b) => a.weight - b.weight,
  },
  {
    title: '合計金額(円)',
    dataIndex: 'amount',
    key: 'amount',
    align: 'right' as const,
    width: 140,
    render: (value: number) => value.toLocaleString(),
    sorter: (a, b) => a.amount - b.amount,
  },
  {
    title: '最終搬入日',
    dataIndex: 'lastDeliveryDate',
    key: 'lastDeliveryDate',
    width: 140,
    sorter: (a, b) => {
      if (!a.lastDeliveryDate) return 1;
      if (!b.lastDeliveryDate) return -1;
      return a.lastDeliveryDate.localeCompare(b.lastDeliveryDate);
    },
    defaultSortOrder: 'descend' as const,
  },
  {
    title: '担当営業者',
    dataIndex: 'sales',
    key: 'sales',
    width: 120,
    sorter: (a, b) => a.sales.localeCompare(b.sales),
  },
];

/**
 * Customer Comparison Result Card
 *
 * 顧客比較結果を表示するカードコンポーネント
 */
const CustomerComparisonResultCard: React.FC<Props> = ({
  title,
  data,
  cardStyle,
  headerStyle,
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
    styles={{
      header: { fontWeight: 600, ...headerStyle },
      body: { flex: 1, minHeight: 0, overflow: 'auto', padding: 0 },
    }}
  >
    <div className="responsive-x" style={{ minHeight: 0, height: '100%' }}>
      <Table
        dataSource={data}
        columns={customerColumns}
        size="small"
        rowKey="key"
        pagination={false}
        locale={{ emptyText: '該当なし' }}
        scroll={{ x: 'max-content', y: 'calc(100vh - 280px)' }}
        sticky
      />
    </div>
  </Card>
);

export default CustomerComparisonResultCard;
