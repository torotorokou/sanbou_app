import React, { useState } from 'react';
import { Card, Typography } from 'antd';
import CsvUploadCard from './CsvUploadCard';
import type { CsvFileType } from './types';
import type { UploadProps } from 'antd';
import { customTokens } from '@/theme/tokens';
import { useDeviceType } from '@/hooks/ui/useResponsive';

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
    const { isMobile, isTablet } = useDeviceType();

    return (
        <Card
            size={isMobile ? 'small' : 'default'}
            title={
                <Typography.Title
                    level={isMobile ? 5 : 4}
                    style={{
                        margin: 0,
                        fontSize: isMobile ? '14px' : isTablet ? '16px' : '18px'
                    }}
                >
                    📂 CSVアップロード
                </Typography.Title>
            }
            style={{
                borderRadius: isMobile ? 8 : 12,
                backgroundColor: customTokens.colorBgBase,
                width: '100%',
                // シンプルな3段階の高さ設定
                maxHeight: isMobile ? 350 : isTablet ? 450 : 500,
                minHeight: isMobile ? 250 : isTablet ? 300 : 350,
                overflowY: 'auto',
            }}
        >
            <div style={{
                display: 'flex',
                flexDirection: 'column',
                gap: isMobile ? 10 : isTablet ? 12 : 16 // シンプルな3段階
            }}>
                {upload.files.map((entry, index) => (
                    <CsvUploadCard
                        key={entry.label}
                        label={entry.label}
                        file={entry.file}
                        required={entry.required}
                        onChange={entry.onChange}
                        uploadProps={upload.makeUploadProps(
                            entry.label,
                            entry.onChange
                        )}
                        isHovering={hoveringIndex === index}
                        onHover={(hover) =>
                            setHoveringIndex(hover ? index : null)
                        }
                        validationResult={entry.validationResult ?? 'unknown'}
                    />
                ))}
            </div>
        </Card>
    );
};

export default CsvUploadPanel;
