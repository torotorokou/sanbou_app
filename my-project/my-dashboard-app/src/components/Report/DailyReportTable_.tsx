import React from 'react';
import { Table, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';

export type ReportRow = {
    key: string;
    工場: string;
    搬入量: number;
    搬出量: number;
};

type DailyReportTableProps = {
    dateLabel: string | undefined;
    data: ReportRow[];
    finalized: boolean;
};

const columns: ColumnsType<ReportRow> = [
    { title: '工場', dataIndex: '工場', key: '工場' },
    { title: '搬入量', dataIndex: '搬入量', key: '搬入量' },
    { title: '搬出量', dataIndex: '搬出量', key: '搬出量' },
];

const DailyReportTable: React.FC<DailyReportTableProps> = ({
    dateLabel,
    data,
    finalized,
}) => {
    return (
        <div style={{ flex: 1 }}>
            <Typography.Title level={4}>
                📄 {dateLabel || ''} の帳簿
            </Typography.Title>
            {finalized ? (
                <Table
                    columns={columns}
                    dataSource={data}
                    pagination={false}
                    bordered
                />
            ) : (
                <Typography.Text type="secondary">
                    帳簿を作成するとここに表示されます。
                </Typography.Text>
            )}
        </div>
    );
};

export default DailyReportTable;
