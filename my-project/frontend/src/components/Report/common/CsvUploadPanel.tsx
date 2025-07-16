import React, { useState } from 'react';
import { Upload, Typography, Card, Tag } from 'antd';
import { InboxOutlined, CloseOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';
import { customTokens } from '@/theme/tokens';

// 型定義をグループ化バージョンに
type CsvFileType = {
    label: string;
    file: File | null;
    onChange: (file: File | null) => void;
    required: boolean; // ✅ 必須フラグ追加
};

type CsvUploadPanelProps = {
    upload: {
        files: CsvFileType[];
        makeUploadProps: (
            label: string,
            setter: (file: File) => void
        ) => UploadProps;
    };
};

const CsvUploadPanel: React.FC<CsvUploadPanelProps> = ({ upload }) => {
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
                {upload.files.map(
                    ({ label, file, onChange, required }, index) => {
                        const isHovering = hoveringIndex === index;

                        return (
                            <div key={label}>
                                <Typography.Text
                                    strong
                                    style={{ fontSize: 14, marginBottom: 4 }}
                                >
                                    {label}
                                    <Tag
                                        color={required ? 'red' : 'blue'}
                                        style={{ marginLeft: 8 }}
                                    >
                                        {required ? '必須' : '任意'}
                                    </Tag>
                                </Typography.Text>

                                <Upload.Dragger
                                    {...upload.makeUploadProps(label, onChange)}
                                    accept='.csv'
                                    maxCount={1}
                                    style={{
                                        position: 'relative',
                                        height: 150,
                                        padding: 8,
                                        fontSize: 13,
                                        lineHeight: 1.5,
                                        display: 'flex',
                                        flexDirection: 'column',
                                        justifyContent: 'center',
                                        alignItems: 'center',
                                        textAlign: 'center',
                                        borderRadius: 8,
                                        backgroundColor: file
                                            ? '#e6ffed'
                                            : isHovering
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
                                        <Typography.Text
                                            style={{ fontSize: 13 }}
                                        >
                                            ファイルを選択またはドロップ
                                        </Typography.Text>
                                        {file ? (
                                            <Tag color='green'>
                                                ✅ {file.name}
                                            </Tag>
                                        ) : (
                                            <Tag color='default'>未選択</Tag>
                                        )}
                                    </div>

                                    {file && (
                                        <CloseOutlined
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                onChange(null);
                                            }}
                                            style={{
                                                position: 'absolute',
                                                top: 8,
                                                right: 8,
                                                cursor: 'pointer',
                                                color: '#ff4d4f',
                                                fontSize: 16,
                                            }}
                                        />
                                    )}
                                </Upload.Dragger>
                            </div>
                        );
                    }
                )}
            </div>
        </Card>
    );
};

export default CsvUploadPanel;
