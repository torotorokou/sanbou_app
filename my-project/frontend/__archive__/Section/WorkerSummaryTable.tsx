// components/Report/WorkerSummaryTable.tsx
import React from 'react';
import { Table, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';

// データ構造の型
export type WorkerRow = {
    氏名: string;
    所属: string;
    出勤区分: string;
    時間帯: '早番' | '遅番';
    配置場所: string; // 第一工場など
};

// 場所×時間帯ごとの集計結果型
type SummaryRow = {
    key: string;
    配置場所: string;
    早番: number;
    遅番: number;
    合計: number;
};

// 集計関数
function summarizeWorkers(data: WorkerRow[]): SummaryRow[] {
    const summaryMap: Record<string, { 早番: number; 遅番: number }> = {};

    data.forEach((row) => {
        const place = row.配置場所;
        if (!summaryMap[place]) {
            summaryMap[place] = { 早番: 0, 遅番: 0 };
        }
        summaryMap[place][row.時間帯] += 1;
    });

    const rows: SummaryRow[] = Object.entries(summaryMap).map(
        ([place, counts], i) => ({
            key: i.toString(),
            配置場所: place,
            早番: counts.早番,
            遅番: counts.遅番,
            合計: counts.早番 + counts.遅番,
        })
    );

    // 合計行
    const total = rows.reduce(
        (acc, row) => {
            acc.早番 += row.早番;
            acc.遅番 += row.遅番;
            acc.合計 += row.合計;
            return acc;
        },
        { 早番: 0, 遅番: 0, 合計: 0 }
    );
    rows.push({ key: 'total', 配置場所: '合計', ...total });

    return rows;
}

const columns: ColumnsType<SummaryRow> = [
    { title: '配置場所', dataIndex: '配置場所', key: '配置場所' },
    { title: '早番', dataIndex: '早番', key: '早番', align: 'right' },
    { title: '遅番', dataIndex: '遅番', key: '遅番', align: 'right' },
    { title: '合計', dataIndex: '合計', key: '合計', align: 'right' },
];

const WorkerSummaryTable: React.FC<{ data: WorkerRow[] }> = ({ data }) => {
    const summary = summarizeWorkers(data);

    return (
        <div>
            <Typography.Title level={5}>👷 出勤者集計表</Typography.Title>
            <Table
                dataSource={summary}
                columns={columns}
                pagination={false}
                bordered
                size='small'
            />
        </div>
    );
};

export default WorkerSummaryTable;
