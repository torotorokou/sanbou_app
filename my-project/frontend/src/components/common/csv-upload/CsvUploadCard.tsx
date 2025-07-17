import React from 'react';
import { Upload, Typography, Tag } from 'antd';
import { InboxOutlined, CloseOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';

export type CsvUploadCardProps = {
    label: string;
    file: File | null;
    required: boolean;
    onChange: (file: File | null) => void;
    uploadProps: UploadProps;
    isHovering: boolean;
    onHover: (hover: boolean) => void;
    validationResult?: 'valid' | 'invalid' | 'unknown';
    onRemove?: () => void;
};

const CsvUploadCard: React.FC<CsvUploadCardProps> = ({
    label,
    file,
    required,
    onChange,
    uploadProps,
    isHovering,
    onHover,
    validationResult = 'unknown',
    onRemove,
}) => {
    // ファイル未選択の時は常にunknown扱いにする
    const effectiveValidationResult = file ? validationResult : 'unknown';

    const getBackgroundColor = () => {
        if (effectiveValidationResult === 'invalid') return '#fff1f0'; // 薄赤
        if (file) return '#e6ffed'; // アップロード済み（緑）
        return '#fafafa';
    };
    const getBorderColor = () => {
        if (effectiveValidationResult === 'invalid') return '#ff4d4f'; // 赤
        return isHovering ? '#22c55e' : '#d9d9d9'; // 緑 or 灰
    };

    return (
        <div>
            <Typography.Text strong style={{ fontSize: 14, marginBottom: 4 }}>
                {label}
                <Tag
                    color={required ? 'red' : 'blue'}
                    style={{ marginLeft: 8 }}
                >
                    {required ? '必須' : '任意'}
                </Tag>
            </Typography.Text>

            <Upload.Dragger
                {...uploadProps}
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
                    backgroundColor: getBackgroundColor(),
                    borderColor: getBorderColor(),
                    borderStyle: 'dashed',
                    borderWidth: 1,
                    boxShadow: isHovering
                        ? '0 2px 8px rgba(34, 197, 94, 0.15)'
                        : undefined,
                    transition: 'all 0.2s ease-in-out',
                }}
                onMouseEnter={() => onHover(true)}
                onMouseLeave={() => onHover(false)}
            >
                <div
                    style={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: 4,
                    }}
                >
                    <InboxOutlined style={{ fontSize: 22, marginBottom: 4 }} />
                    <Typography.Text style={{ fontSize: 13 }}>
                        ファイルを選択またはドロップ
                    </Typography.Text>
                    {file ? (
                        <Tag
                            color={
                                effectiveValidationResult === 'invalid'
                                    ? 'red'
                                    : 'green'
                            }
                        >
                            {effectiveValidationResult === 'invalid'
                                ? '⚠ 不正なCSV'
                                : `✅ ${file.name}`}
                        </Tag>
                    ) : (
                        <Typography.Text
                            type='secondary'
                            style={{ fontSize: 12 }}
                        >
                            未選択
                        </Typography.Text>
                    )}
                    {effectiveValidationResult === 'invalid' && (
                        <Typography.Text type='danger' style={{ fontSize: 12 }}>
                            想定されたCSV形式と異なります。
                        </Typography.Text>
                    )}
                </div>

                {file && (
                    <CloseOutlined
                        onClick={(e) => {
                            e.stopPropagation();
                            if (onRemove) {
                                onRemove();
                            } else {
                                onChange(null);
                            }
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
};

export default CsvUploadCard;
