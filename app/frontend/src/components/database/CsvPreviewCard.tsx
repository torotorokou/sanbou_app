import React from 'react';
import { Card, Empty } from 'antd';
import AutoHeightTable from '@/components/table/AutoHeightTable';
import type { UploadCsvType } from '@/constants/uploadCsvConfig';
import { UPLOAD_CSV_DEFINITIONS } from '@/constants/uploadCsvConfig';

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
    backgroundColor?: string;
};

export const CsvPreviewCard: React.FC<Props> = ({
    type,
    csvPreview,
    validationResult,
    cardHeight = 300,
    backgroundColor: propBackgroundColor,
}) => {
    const backgroundColor = propBackgroundColor || CSV_TYPE_COLORS[type] || '#ffffff';

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
                height: cardHeight - 48,
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden',
            }}
            style={{
                height: cardHeight,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'flex-start',
            }}
        >
            {csvPreview && csvPreview.rows.length > 0 ? (
                <div className="table-wrap" style={{ flex: 1 }}>
                    <AutoHeightTable
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
                        scroll={{ x: Math.max(csvPreview.columns.length * 120, 800) }}
                        bordered
                        rowKey={(_, i) => (i ?? 0).toString()}
                        style={{ minWidth: csvPreview.columns.length * 120 }}
                    />
                </div>
            ) : (
                <Empty description='プレビューなし' />
            )}
        </Card>
    );
};

export default CsvPreviewCard;
