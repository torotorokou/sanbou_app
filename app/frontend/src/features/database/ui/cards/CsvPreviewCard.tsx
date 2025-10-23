import React, { useEffect, useRef, useState } from 'react';
import { Card, Table, Empty } from 'antd';
import type { UploadCsvType } from '../../domain/config/uploadCsvConfig';
import { UPLOAD_CSV_DEFINITIONS } from '../../domain/config/uploadCsvConfig';

// 色マップを定義（CSVタイプごとに色を分ける）
const CSV_TYPE_COLORS: Record<UploadCsvType, string> = {
    receive: '#f0f7e8ff',  // 赤系（受入）
    shipment: '#ffffffff', // 青系（出荷）
    yard: '#ffffffff',     // 緑系（ヤード）
};

type Props = {
    type: UploadCsvType;
    csvPreview: { columns: string[]; rows: string[][] } | null;
    validationResult: 'valid' | 'invalid' | 'unknown';
    cardHeight?: number;
    tableBodyHeight?: number;
    backgroundColor?: string;
};

export const CsvPreviewCard: React.FC<Props> = ({
    type,
    csvPreview,
    validationResult,
    cardHeight = 300,
    tableBodyHeight = 220,
    backgroundColor: propBackgroundColor,
}) => {
    const backgroundColor = propBackgroundColor || CSV_TYPE_COLORS[type] || '#ffffff';

    const wrapperRef = useRef<HTMLDivElement | null>(null);
    const [measuredTableHeight, setMeasuredTableHeight] = useState<number | null>(null);

    useEffect(() => {
        const el = wrapperRef.current;
        if (!el) return;
        const update = () => {
            // measure available height for the table inside the card
            const h = el.clientHeight;
            setMeasuredTableHeight(h);
        };
        update();
        const ro = new ResizeObserver(update);
        ro.observe(el);
        return () => ro.disconnect();
    }, [cardHeight, tableBodyHeight]);

    const usedTableHeight = tableBodyHeight ?? measuredTableHeight ?? Math.max(80, Math.floor(cardHeight * 0.6));

    return (
        <Card
            title={
                <span>
                    {UPLOAD_CSV_DEFINITIONS[type].label}
                    {!UPLOAD_CSV_DEFINITIONS[type].required && (
                        <span
                            style={{
                                color: '#1890ff',
                                marginLeft: 8,
                                fontSize: 13,
                            }}
                        >
                            任意
                        </span>
                    )}
                    プレビュー
                    {validationResult === 'valid' ? (
                        <span style={{ color: 'green', marginLeft: 12 }}>
                            ✅ 有効
                        </span>
                    ) : validationResult === 'invalid' ? (
                        <span style={{ color: 'red', marginLeft: 12 }}>
                            ❌ 無効
                        </span>
                    ) : (
                        <span style={{ color: 'gray', marginLeft: 12 }}>
                            未判定
                        </span>
                    )}
                </span>
            }
            size='small'
            headStyle={{ backgroundColor }}
            bodyStyle={{
                padding: 8,
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden',
                boxSizing: 'border-box',
            }}
            style={{
                height: cardHeight,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'flex-start',
            }}
        >
            {csvPreview && csvPreview.rows.length > 0 ? (
                <div
                        className="responsive-x"
                    ref={wrapperRef}
                    style={{
                        flex: 1,
                        width: '100%',
                        overflow: 'hidden',
                        // let the antd Table handle horizontal scrolling to avoid duplicate scrollbars
                        overflowX: 'hidden',
                        display: 'flex',
                        flexDirection: 'column',
                        // constrain the visible table area to the provided/measured height so it matches the card
                        maxHeight: usedTableHeight,
                    }}
                >
                    <Table
                        columns={csvPreview.columns.map((col, i) => ({
                            title: col,
                            dataIndex: i,
                            key: i,
                            width: 120,
                            ellipsis: true,
                        }))}
                        dataSource={csvPreview.rows.map((row) =>
                            Object.fromEntries(row.map((v, ci) => [ci, v]))
                        )}
                        pagination={false}
                        size='small'
                        // calculate horizontal scroll width from column count
                        scroll={{ y: usedTableHeight, x: Math.max(csvPreview.columns.length * 120, 800) }}
                        bordered
                        rowKey={(_, i) => (i ?? 0).toString()}
                        style={{ minWidth: csvPreview.columns.length * 120, flex: '0 0 auto' }}
                    />
                </div>
            ) : (
                <Empty description='プレビューなし' />
            )}
        </Card>
    );
};

export default CsvPreviewCard;
