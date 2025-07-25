import React, { useState } from 'react';
import { Card, Typography } from 'antd';
import CsvUploadCard from './CsvUploadCard';
import type { CsvFileType } from './types';
import type { UploadProps } from 'antd';
import { customTokens } from '@/theme/tokens';

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
