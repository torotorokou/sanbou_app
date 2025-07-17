import React, { useState } from 'react';
import { Row, Col, Card, Table, Empty } from 'antd';
import CsvUploadPanel from '@/components/common/csv-upload/CsvUploadPanel';
import { CSV_DEFINITIONS } from '@/constants/csvTypes';
import type { CsvType } from '@/constants/csvTypes';
import { identifyCsvType, isCsvMatch } from '@/utils/validators/csvValidator';

const CSV_TYPES: CsvType[] = ['shipment', 'receive', 'yard'];

type CsvData = {
    columns: string[];
    rows: string[][];
};

const CARD_HEIGHT = 280; // 1カードの高さ（適宜調整）
const TABLE_BODY_HEIGHT = 160; // Table部の高さ

const DatabaseCsvUploadArea: React.FC = () => {
    const [files, setFiles] = useState<Record<CsvType, File | null>>(
        () =>
            Object.fromEntries(CSV_TYPES.map((type) => [type, null])) as Record<
                CsvType,
                File | null
            >
    );
    const [validationResults, setValidationResults] = useState<
        Record<CsvType, 'valid' | 'invalid' | 'unknown'>
    >(
        () =>
            Object.fromEntries(
                CSV_TYPES.map((type) => [type, 'unknown'])
            ) as Record<CsvType, 'valid' | 'invalid' | 'unknown'>
    );
    const [csvPreviews, setCsvPreviews] = useState<
        Record<CsvType, CsvData | null>
    >(
        () =>
            Object.fromEntries(CSV_TYPES.map((type) => [type, null])) as Record<
                CsvType,
                CsvData | null
            >
    );

    const labelToType = Object.fromEntries(
        CSV_TYPES.map((type) => [CSV_DEFINITIONS[type].label, type])
    ) as Record<string, CsvType>;

    const parseCsvPreview = (text: string): CsvData => {
        const lines = text.split(/\r?\n/).filter((l) => l.trim() !== '');
        if (lines.length === 0) return { columns: [], rows: [] };
        const columns = lines[0].split(',');
        const rows = lines.slice(1, 16).map((row) => row.split(','));
        return { columns, rows };
    };

    const makeUploadProps = (
        label: string,
        onChange: (file: File | null) => void
    ) => ({
        accept: '.csv',
        showUploadList: false,
        beforeUpload: (file: File) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const text = e.target?.result as string;
                const type = labelToType[label];
                setCsvPreviews((prev) => ({
                    ...prev,
                    [type]: parseCsvPreview(text),
                }));
                if (!type) {
                    setValidationResults((prev) => ({
                        ...prev,
                        [type]: 'invalid',
                    }));
                    onChange(null);
                    return;
                }
                const result = identifyCsvType(text);
                const isValid = isCsvMatch(result, label);
                setValidationResults((prev) => ({
                    ...prev,
                    [type]: isValid ? 'valid' : 'invalid',
                }));
                onChange(file);
            };
            reader.readAsText(file);
            return false;
        },
    });

    const panelFiles = CSV_TYPES.map((type) => ({
        label: CSV_DEFINITIONS[type].label,
        file: files[type],
        required: false,
        onChange: (f: File | null) => {
            setFiles((prev) => ({ ...prev, [type]: f }));
            if (!f) setCsvPreviews((prev) => ({ ...prev, [type]: null }));
        },
        validationResult: validationResults[type],
        onRemove: () => {
            setFiles((prev) => ({ ...prev, [type]: null }));
            setValidationResults((prev) => ({ ...prev, [type]: 'unknown' }));
            setCsvPreviews((prev) => ({ ...prev, [type]: null }));
        },
    }));

    return (
        <Row style={{ height: '100vh', minHeight: 600 }}>
            {/* 左: アップロード */}
            <Col span={8} style={{ padding: 16, height: '100%' }}>
                <CsvUploadPanel
                    upload={{
                        files: panelFiles,
                        makeUploadProps: (label, onChange) =>
                            makeUploadProps(label, onChange),
                    }}
                />
            </Col>
            {/* 右: プレビュー（縦3つ、全体スクロール） */}
            <Col
                span={16}
                style={{
                    padding: 16,
                    height: '100%',
                    overflowY: 'auto',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 16,
                }}
            >
                {CSV_TYPES.map((type) => (
                    <Card
                        key={type}
                        title={
                            <span>
                                {CSV_DEFINITIONS[type].label} プレビュー
                                {validationResults[type] === 'valid' ? (
                                    <span
                                        style={{
                                            color: 'green',
                                            marginLeft: 12,
                                        }}
                                    >
                                        ✅ 有効
                                    </span>
                                ) : validationResults[type] === 'invalid' ? (
                                    <span
                                        style={{ color: 'red', marginLeft: 12 }}
                                    >
                                        ❌ 無効
                                    </span>
                                ) : (
                                    <span
                                        style={{
                                            color: 'gray',
                                            marginLeft: 12,
                                        }}
                                    >
                                        未判定
                                    </span>
                                )}
                            </span>
                        }
                        size='small'
                        bodyStyle={{ padding: 8 }}
                        style={{
                            height: CARD_HEIGHT,
                            overflow: 'hidden',
                            display: 'flex',
                            flexDirection: 'column',
                            justifyContent: 'flex-start',
                        }}
                    >
                        {csvPreviews[type] &&
                        csvPreviews[type]?.rows.length > 0 ? (
                            <Table
                                columns={csvPreviews[type]?.columns.map(
                                    (col, i) => ({
                                        title: col,
                                        dataIndex: i,
                                        key: i,
                                        width: 120,
                                        ellipsis: true,
                                    })
                                )}
                                dataSource={csvPreviews[type]?.rows.map(
                                    (row, ri) =>
                                        Object.fromEntries(
                                            row.map((v, ci) => [ci, v])
                                        )
                                )}
                                pagination={false}
                                size='small'
                                scroll={{
                                    y: TABLE_BODY_HEIGHT,
                                    x: 'max-content',
                                }}
                                bordered
                                rowKey={(_, i) => i.toString()}
                                style={{ flex: 1 }}
                            />
                        ) : (
                            <Empty description='プレビューなし' />
                        )}
                    </Card>
                ))}
            </Col>
        </Row>
    );
};

export default DatabaseCsvUploadArea;
