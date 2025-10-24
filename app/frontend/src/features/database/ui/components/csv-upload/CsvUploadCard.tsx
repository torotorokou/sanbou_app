import React from 'react';
import { Upload, Typography, Tag } from 'antd';
import { InboxOutlined, CloseOutlined } from '@ant-design/icons';
import { useResponsive } from '@/shared';
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
    cardHeight?: number; // 動的な高さ
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
    cardHeight, // 動的な高さを受け取る
}) => {
    const { isMobile, isTablet } = useResponsive();
    const isMobileOrTablet = isMobile || isTablet;

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
            <Typography.Text strong style={{
                fontSize: isMobile ? 12 : 13, // ラベルのフォントサイズを小さく
                marginBottom: 2, // マージンを縮小
                display: 'block'
            }}>
                {label}
                <Tag
                    color={required ? 'red' : 'blue'}
                    style={{
                        marginLeft: isMobile ? 3 : 6, // マージンを縮小
                        fontSize: isMobile ? '9px' : '10px' // タグのフォントを小さく
                    }}
                >
                    {required ? '必須' : '任意'}
                </Tag>
            </Typography.Text>

            <div
                onMouseEnter={() => onHover(true)}
                onMouseLeave={() => onHover(false)}
                style={{
                    // 動的な高さ（デフォルト値も設定）
                    height: cardHeight || (isMobile ? 70 : isMobileOrTablet ? 80 : 90),
                    borderRadius: isMobile ? 6 : 8,
                }}
            >
                <Upload.Dragger
                    {...uploadProps}
                    accept='.csv'
                    maxCount={1}
                    style={{
                        position: 'relative',
                        height: '100%',
                        padding: isMobile ? 3 : 4, // パディングをさらに小さく
                        fontSize: isMobile ? 10 : 11, // フォントサイズを小さく
                        lineHeight: 1.3, // 行間を縮小
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'center',
                        alignItems: 'center',
                        textAlign: 'center',
                        borderRadius: isMobile ? 6 : 8,
                        backgroundColor: getBackgroundColor(),
                        borderColor: getBorderColor(),
                        borderStyle: 'dashed',
                        borderWidth: 1,
                        boxShadow: isHovering
                            ? '0 2px 8px rgba(34, 197, 94, 0.15)'
                            : undefined,
                        transition: 'all 0.2s ease-in-out',
                    }}
                >
                    <div
                        style={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            gap: isMobile ? 3 : 4,
                        }}
                    >
                        <InboxOutlined style={{
                            fontSize: isMobile ? 18 : 22,
                            marginBottom: isMobile ? 2 : 4
                        }} />
                        <Typography.Text style={{
                            fontSize: isMobile ? 11 : 13,
                            textAlign: 'center'
                        }}>
                            ファイルを選択またはドロップ
                        </Typography.Text>
                        {file ? (
                            <Tag
                                color={
                                    effectiveValidationResult === 'invalid'
                                        ? 'red'
                                        : 'green'
                                }
                                style={{
                                    fontSize: isMobile ? '10px' : '12px',
                                    maxWidth: isMobile ? '90%' : 'none',
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    whiteSpace: 'nowrap'
                                }}
                            >
                                {effectiveValidationResult === 'invalid'
                                    ? '⚠ 不正なCSV'
                                    : `✅ ${isMobile && file.name.length > 15
                                        ? file.name.substring(0, 15) + '...'
                                        : file.name}`}
                            </Tag>
                        ) : (
                            <Typography.Text
                                type='secondary'
                                style={{ fontSize: isMobile ? 10 : 12 }}
                            >
                                未選択
                            </Typography.Text>
                        )}
                        {effectiveValidationResult === 'invalid' && (
                            <Typography.Text
                                type='danger'
                                style={{
                                    fontSize: isMobile ? 10 : 12,
                                    textAlign: 'center',
                                    lineHeight: 1.3
                                }}
                            >
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
                                top: isMobile ? 6 : 8,
                                right: isMobile ? 6 : 8,
                                cursor: 'pointer',
                                color: '#ff4d4f',
                                fontSize: isMobile ? 14 : 16,
                                zIndex: 10,
                                padding: 2,
                                backgroundColor: 'rgba(255, 255, 255, 0.8)',
                                borderRadius: '50%',
                            }}
                        />
                    )}
                </Upload.Dragger>
            </div>
        </div>
    );
};

export default CsvUploadCard;
