import React, { useMemo, useState } from 'react';
import { DatePicker, Select, Space, Button, Pagination } from 'antd';
import { AutoHeightTable as Table } from '@/components/table/AutoHeightTable';
import dayjs from 'dayjs';
import type { Dayjs } from 'dayjs';
import isSameOrAfter from 'dayjs/plugin/isSameOrAfter';
import isSameOrBefore from 'dayjs/plugin/isSameOrBefore';
import {
    useReactTable,
    getCoreRowModel,
    getFilteredRowModel,
    getPaginationRowModel,
    getSortedRowModel,
    type ColumnDef,
    type ColumnFiltersState,
    type SortingState,
} from '@tanstack/react-table';

dayjs.extend(isSameOrAfter);
dayjs.extend(isSameOrBefore);

const { MonthPicker, RangePicker } = DatePicker;

type RecordType = { [key: string]: string | number | null };
import dummyData from '../../data/受入一覧_20250501_clean.json';

// ユニークキーに使用するカラム
const unique_keys = ['伝票日付', '業者名', '品名', '受入番号', '正味重量'];

const visibleColumns = [
    { key: '受入番号', width: 100, type: 'int' as const },
    { key: '伝票日付', width: 110, type: 'date' as const },
    { key: '業者名', width: 160, type: 'string' as const },
    { key: '品名', width: 120, type: 'string' as const },
    { key: '正味重量', width: 90, type: 'float' as const },
    { key: '金額', width: 90, type: 'int' as const },
    { key: '単価', width: 80, type: 'float' as const },
    { key: '種類名', width: 90, type: 'string' as const },
    { key: '運搬業者名', width: 110, type: 'string' as const },
    { key: '営業担当者名', width: 100, type: 'string' as const },
] as const;

const RecordListPage: React.FC = () => {
    const [month, setMonth] = useState<Dayjs>(dayjs('2025-07'));
    const [dateRange, setDateRange] = useState<[Dayjs | null, Dayjs | null]>([null, null]);
    const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
    const [sorting, setSorting] = useState<SortingState>([]);
    const [pageIndex, setPageIndex] = useState(0);
    const [pageSize, setPageSize] = useState(10);

    // フィルタ適用データ
    const filteredData = useMemo(() => {
        const selectedMonth = month.format('YYYY-MM');
        const strFilters: { [key: string]: string[] } = {};
        visibleColumns.forEach(col => {
            if (col.type === 'string') {
                const val = columnFilters.find(f => f.id === col.key)?.value;
                if (Array.isArray(val) && val.length > 0) {
                    strFilters[col.key] = val as string[];
                }
            }
        });
        return dummyData.filter((record: RecordType) => {
            // 月フィルター
            const rawDate = record['伝票日付'];
            if (typeof rawDate !== 'string') return false;
            const parsed = dayjs(rawDate, 'YYYY/MM/DD');
            if (!parsed.isValid() || parsed.format('YYYY-MM') !== selectedMonth) return false;

            // 伝票日付範囲フィルター
            if (dateRange[0] && dateRange[1]) {
                if (!(parsed.isSameOrAfter(dateRange[0], 'day') && parsed.isSameOrBefore(dateRange[1], 'day'))) return false;
            } else if (dateRange[0]) {
                if (!parsed.isSameOrAfter(dateRange[0], 'day')) return false;
            } else if (dateRange[1]) {
                if (!parsed.isSameOrBefore(dateRange[1], 'day')) return false;
            }

            // string型フィルター
            for (const key of Object.keys(strFilters)) {
                const val = record[key];
                if (!strFilters[key].includes(String(val))) {
                    return false;
                }
            }
            return true;
        });
    }, [month, dateRange, columnFilters]);

    // TanStack Table カラム定義
    const columns = useMemo<ColumnDef<RecordType>[]>(() =>
        visibleColumns.map(col => ({
            accessorKey: col.key,
            header: col.key,
            cell: info => info.getValue(),
        })),
        []
    );

    // TanStack Tableインスタンス
    const table = useReactTable({
        data: filteredData,
        columns,
        state: {
            columnFilters,
            sorting,
            pagination: { pageIndex, pageSize },
        },
        onColumnFiltersChange: setColumnFilters,
        onSortingChange: setSorting,
        onPaginationChange: updater => {
            if (typeof updater === 'function') {
                const newState = updater({ pageIndex, pageSize });
                setPageIndex(newState.pageIndex);
                setPageSize(newState.pageSize);
            } else if (typeof updater === 'object') {
                setPageIndex(updater.pageIndex ?? pageIndex);
                setPageSize(updater.pageSize ?? pageSize);
            }
        },
        getCoreRowModel: getCoreRowModel(),
        getFilteredRowModel: getFilteredRowModel(),
        getSortedRowModel: getSortedRowModel(),
        getPaginationRowModel: getPaginationRowModel(),
        manualPagination: false,
        manualSorting: false,
    });

    // string型カラムのフィルター選択肢
    const dynamicOptionsMap = useMemo(() => {
        const map: { [key: string]: string[] } = {};
        visibleColumns.forEach(col => {
            if (col.type === 'string') {
                let filtered = filteredData;
                for (const key of visibleColumns.filter(v => v.type === 'string' && v.key !== col.key).map(v => v.key)) {
                    const selected = columnFilters.find(f => f.id === key)?.value as string[] | undefined;
                    if (selected && selected.length > 0) {
                        filtered = filtered.filter(row => selected.includes(String(row[key] ?? '')));
                    }
                }
                const values = Array.from(new Set(filtered.map(row => String(row[col.key] ?? '')).filter(v => v !== '')));
                map[col.key] = values.sort((a, b) => a.localeCompare(b, 'ja'));
            }
        });
        return map;
    }, [filteredData, columnFilters]);

    // AntD Table columns
    const antColumns = useMemo(
        () =>
            visibleColumns.map(col => {
                let filterUI: React.ReactNode = null;
                if (col.type === 'string') {
                    filterUI = (
                        <Select
                            allowClear
                            mode="multiple"
                            placeholder="全て"
                            style={{ width: col.width - 8, fontSize: 12 }}
                            value={
                                (columnFilters.find((f) => f.id === col.key)?.value as string[]) ?? []
                            }
                            onChange={v => {
                                table.setPageIndex(0);
                                setColumnFilters((old) =>
                                    v && v.length > 0
                                        ? [...old.filter(f => f.id !== col.key), { id: col.key, value: v }]
                                        : old.filter(f => f.id !== col.key)
                                );
                            }}
                            size="small"
                            options={dynamicOptionsMap[col.key]?.map(val => ({
                                label: val,
                                value: val,
                            }))}
                        />
                    );
                }

                // ソートはTanStack Tableで行うので、AntD Tableには付けない
                return {
                    title: (
                        <div>
                            <div>{col.key}</div>
                            {filterUI}
                        </div>
                    ),
                    dataIndex: col.key,
                    key: col.key,
                    width: col.width,
                    render: (value: string | number) => (
                        <div
                            className="cell-xscroll"
                            style={{
                                width: col.width,
                                minWidth: col.width,
                                maxWidth: col.width,
                            }}
                            title={String(value)}
                        >
                            {value}
                        </div>
                    ),
                };
            }),
        [columnFilters, dynamicOptionsMap, table]
    );

    return (
        <div style={{ padding: 24 }}>
            <style>
                {`
            .table-row-even td {
                background-color: #f7fcf9 !important;
            }
            .table-row-odd td {
                background-color: #fff !important;
            }
        `}
            </style>
            <h2>受入一覧（月・日付範囲・TanStackページネーション・str型フィルター対応）</h2>
            <div style={{ marginBottom: 16 }}>
                <Space>
                    <span>
                        <label style={{ marginRight: 8 }}>対象月:</label>
                        <MonthPicker
                            value={month}
                            onChange={date => {
                                table.setPageIndex(0);
                                if (date) setMonth(date);
                            }}
                            format="YYYY-MM"
                            allowClear={false}
                        />
                    </span>
                    <span>
                        <label style={{ margin: '0 8px 0 16px' }}>伝票日付範囲:</label>
                        <RangePicker
                            value={dateRange}
                            onChange={dates => {
                                table.setPageIndex(0);
                                setDateRange(dates ?? [null, null]);
                            }}
                            format="YYYY/MM/DD"
                            allowClear
                            style={{ width: 260 }}
                            disabledDate={current => {
                                if (!month) return false;
                                const startOfMonth = month.startOf('month');
                                const endOfMonth = month.endOf('month');
                                return (
                                    current < startOfMonth.startOf('day') ||
                                    current > endOfMonth.endOf('day')
                                );
                            }}
                        />
                        <Button
                            size="small"
                            style={{ marginLeft: 8 }}
                            onClick={() => {
                                table.setPageIndex(0);
                                setDateRange([null, null]);
                            }}
                        >
                            フィルター解除
                        </Button>
                    </span>
                </Space>
            </div>
            <div className="table-wrap">
                <Table
                    columns={antColumns}
                    dataSource={table.getRowModel().rows.map(row => row.original)}
                    rowKey={record => unique_keys.map(key => String(record[key])).join('_')}
                    scroll={{ x: 'max-content' }}
                    pagination={false}
                    rowClassName={(_, idx) =>
                        idx % 2 === 0 ? 'table-row-even' : 'table-row-odd'
                    }
                />
            </div>
            <div style={{ textAlign: 'right', marginTop: 10 }}>
                <Pagination
                    current={table.getState().pagination.pageIndex + 1}
                    pageSize={table.getState().pagination.pageSize}
                    total={table.getFilteredRowModel().rows.length}
                    showSizeChanger
                    pageSizeOptions={['10', '20', '50', '100']}
                    onChange={(page, pageSize) => {
                        table.setPageIndex(page - 1);
                        table.setPageSize(pageSize || 10);
                    }}
                />
            </div>
        </div>
    );
};

export default RecordListPage;
