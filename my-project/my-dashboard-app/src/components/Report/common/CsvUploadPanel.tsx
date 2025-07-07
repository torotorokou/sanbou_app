import React, { useState } from 'react';
import { Upload, Typography, Card } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
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
    const [hoveringIndex, setHoveringIndex] = useState<number | null>(null);

    return (
        <Card
            size='small'
            title={
                <Typography.Title level={5} style={{ margin: 0 }}>
                    📂 CSVアップロード
                </Typography.Title>
            }
            style={{
                borderRadius: 12,
                backgroundColor: customTokens.colorBgBase,
                width: '100%',
                maxHeight: 850,
                overflowY: 'auto',
            }}
        >
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                {files.map(({ label, file, onChange }, index) => {
                    const isHovering = hoveringIndex === index;

                    return (
                        <div key={label}>
                            <Typography.Text
                                strong
                                style={{ fontSize: 14, marginBottom: 4 }}
                            >
                                {label}
                            </Typography.Text>

                            <Upload.Dragger
                                {...makeUploadProps(label, onChange)}
                                accept='.csv'
                                maxCount={1}
                                style={{
                                    height: 160, // ✅ 高さはこのまま
                                    padding: 12,
                                    fontSize: 13,
                                    lineHeight: 1.5,
                                    display: 'flex',
                                    flexDirection: 'column',
                                    justifyContent: 'center',
                                    alignItems: 'center',
                                    textAlign: 'center',
                                    borderRadius: 8,
                                    backgroundColor: isHovering
                                        ? '#f0fdf4'
                                        : '#fafafa',
                                    borderColor: isHovering
                                        ? '#22c55e'
                                        : '#d9d9d9',
                                    borderStyle: 'dashed',
                                    borderWidth: 1,
                                    boxShadow: isHovering
                                        ? '0 2px 8px rgba(34, 197, 94, 0.15)'
                                        : undefined,
                                    transition: 'all 0.2s ease-in-out',
                                }}
                                onMouseEnter={() => setHoveringIndex(index)}
                                onMouseLeave={() => setHoveringIndex(null)}
                            >
                                <div
                                    style={{
                                        display: 'flex',
                                        flexDirection: 'column',
                                        alignItems: 'center',
                                        gap: 4,
                                    }}
                                >
                                    <InboxOutlined
                                        style={{
                                            fontSize: 22,
                                            marginBottom: 4,
                                        }}
                                    />
                                    <Typography.Text style={{ fontSize: 13 }}>
                                        ファイルを選択またはドロップ
                                    </Typography.Text>
                                    <Typography.Text
                                        type='secondary'
                                        style={{ fontSize: 12 }}
                                    >
                                        {file?.name ? (
                                            <strong
                                                style={{ color: '#16734f' }}
                                            >
                                                {file.name}
                                            </strong>
                                        ) : (
                                            'ファイルが未選択です'
                                        )}
                                    </Typography.Text>
                                </div>
                            </Upload.Dragger>
                        </div>
                    );
                })}
            </div>
        </Card>
    );
};

export default CsvUploadPanel;
