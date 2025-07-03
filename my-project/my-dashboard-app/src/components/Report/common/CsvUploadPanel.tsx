// src/components/Reportcommon/CsvUploadPanel.tsx

import React from 'react';
import { Upload, Button, Typography, Card } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';
import { customTokens } from '@/theme/tokens';

type CsvFileType = {
    label: string;
    file: File | null;
    onChange: (file: File) => void;
};

type CsvUploadPanelProps = {
    files: CsvFileType[];
    makeUploadProps: (
        label: string,
        setter: (file: File) => void
    ) => UploadProps;
};

const CsvUploadPanel: React.FC<CsvUploadPanelProps> = ({
    files,
    makeUploadProps,
}) => {
    return (
        <Card
            size="small"
            title={
                <Typography.Title level={5} style={{ margin: 0 }}>
                    📂 CSVアップロード
                </Typography.Title>
            }
            style={{
                borderRadius: 12,
                backgroundColor: customTokens.colorBgBase,
            }}
        >
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {files.map(({ label, file, onChange }) => (
                    <div
                        key={label}
                        style={{
                            display: 'flex',
                            flexDirection: 'column',
                            gap: 4,
                        }}
                    >
                        <div
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: 12,
                            }}
                        >
                            <Typography.Text style={{ width: 80 }}>
                                {label}
                            </Typography.Text>
                            <Upload {...makeUploadProps(label, onChange)}>
                                <Button
                                    icon={<UploadOutlined />}
                                    type="default"
                                    size="middle"
                                >
                                    アップロード
                                </Button>
                            </Upload>
                        </div>
                        <div
                            style={{
                                minHeight: 22,
                                marginLeft: 92,
                                background: file ? '#f0fdf4' : undefined,
                                border: file ? '1px solid #86efac' : undefined,
                                borderRadius: file ? 6 : undefined,
                                padding: file ? '2px 8px' : undefined,
                                fontSize: 12,
                                color: '#166534',
                            }}
                        >
                            {file?.name || '　'}
                        </div>
                    </div>
                ))}
            </div>
        </Card>
    );
};

export default CsvUploadPanel;
