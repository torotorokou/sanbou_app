import React, { useState } from 'react';
import { Card, Typography } from 'antd';
import CsvUploadCard from '@/components/common/csv-upload/CsvUploadCard';
import type { CsvFileType } from '@features/database';
import type { UploadProps } from 'antd';
import { customTokens } from '@/theme/tokens'; // tsconfigのalias設定が必要

interface CsvUploadCardEntry extends CsvFileType {
    onRemove: () => void;
    validationResult?: 'ok' | 'ng' | 'unknown';
    label: string;
    file: File | null;
    required: boolean;
    onChange: (file: File | null) => void;
}

type CsvUploadPanelProps = {
    upload: {
        files: Array<CsvUploadCardEntry>;
        makeUploadProps: (
            label: string,
            setter: (file: File | null) => void
        ) => UploadProps;
    };
};

const CsvUploadPanel: React.FC<CsvUploadPanelProps> = ({ upload }) => {
    const [hoveringIndex, setHoveringIndex] = useState<number | null>(null);

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
                width: '100%',
            }}
        >
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                {upload.files.map((entry: CsvUploadCardEntry, index: number) => (
                    <CsvUploadCard
                        key={entry.label}
                        label={entry.label}
                        file={entry.file}
                        required={entry.required}
                        onChange={entry.onChange}
                        uploadProps={upload.makeUploadProps(entry.label, entry.onChange)}
                        isHovering={hoveringIndex === index}
                        onHover={(hover: boolean) => setHoveringIndex(hover ? index : null)}
                        validationResult={
                            entry.validationResult === 'ok' ? 'valid' :
                                entry.validationResult === 'ng' ? 'invalid' :
                                    'unknown'
                        }
                        onRemove={entry.onRemove}
                    />
                ))}
            </div>
        </Card>
    );
};

export default CsvUploadPanel;
