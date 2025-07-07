// components/Report/Section/WorkerTable.tsx
import { Table, Typography } from 'antd';
import { WorkerRow } from '@/types/FactoryReportTypes';

const columns = [
    { title: '氏名', dataIndex: '氏名' },
    { title: '所属', dataIndex: '所属' },
    { title: '出勤区分', dataIndex: '出勤区分' },
];

const ShipmentTable = ({ data }: { data: WorkerRow[] }) => (
    <>
        <Typography.Title level={5}>🚚 出荷者一覧</Typography.Title>
        <Table
            columns={columns}
            dataSource={data}
            pagination={false}
            bordered
            size='small'
        />
    </>
);

export default ShipmentTable;
