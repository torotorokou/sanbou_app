import React from 'react';
import { Typography, Col, Row, Button, Modal, Spin } from 'antd';
import CsvUploadPanel from '../../components/database/CsvUploadPanel';
import CsvPreviewCard from '../../components/database/CsvPreviewCard';
import { csvTypeColors } from '../../theme';

import { UploadInstructions } from '@/components/database/UploadInstructions';
import { useCsvUploadHandler } from '@/hooks/database/useCsvUploadHandler';
import { useCsvUploadArea } from '@/hooks/database/useCsvUploadArea';
import { UPLOAD_CSV_TYPES, UPLOAD_CSV_DEFINITIONS } from '@/constants/uploadCsvConfig';

const { Text } = Typography;
const CARD_HEIGHT = 300;
// AutoHeightTable を使用するためTABLE_BODY_HEIGHTは不要

const UploadDatabasePage: React.FC = () => {
    const {
        files,
        validationResults,
        csvPreviews,
        canUpload,
        handleCsvFile,
        removeCsvFile,
    } = useCsvUploadArea();

    const { uploading, handleUpload } = useCsvUploadHandler(files);

    const panelFiles = UPLOAD_CSV_TYPES.map((type) => ({
        label: UPLOAD_CSV_DEFINITIONS[type].label,
        file: files[type],
        required: UPLOAD_CSV_DEFINITIONS[type].required,
        onChange: (f: File | null) => f && handleCsvFile(UPLOAD_CSV_DEFINITIONS[type].label, f),
        validationResult: (validationResults[type] === 'valid' ? 'ok' :
            validationResults[type] === 'invalid' ? 'ng' : 'unknown') as 'ok' | 'ng' | 'unknown',
        onRemove: () => removeCsvFile(type),
    }));

    return (
        <>
            <Row>
                <Col
                    span={8}
                    style={{ padding: 16 }}
                >
                    <UploadInstructions />

                    <CsvUploadPanel
                        upload={{
                            files: panelFiles,
                            makeUploadProps: (label) => ({
                                accept: '.csv',
                                showUploadList: false,
                                beforeUpload: (file: File) => {
                                    handleCsvFile(label, file);
                                    return false;
                                },
                            }),
                        }}
                    />

                    <Button
                        type="primary"
                        disabled={!canUpload}
                        onClick={handleUpload}
                        style={{ marginTop: 24, width: '100%' }}
                    >
                        アップロードする
                    </Button>
                </Col>

                <Col span={16} style={{ padding: 16 }}>
                    {UPLOAD_CSV_TYPES.map((type) => (
                        <CsvPreviewCard
                            key={type}
                            type={type}
                            csvPreview={csvPreviews[type]}
                            validationResult={validationResults[type]}
                            cardHeight={CARD_HEIGHT}
                            backgroundColor={csvTypeColors[type as keyof typeof csvTypeColors]}
                        />
                    ))}
                </Col>
            </Row>

            <Modal
                open={uploading}
                footer={null}
                closable={false}
                centered
                maskClosable={false}
                maskStyle={{ backdropFilter: 'blur(2px)' }}
            >
                <div style={{ textAlign: 'center', padding: '2rem' }}>
                    <Spin size="large" tip="アップロード中です…" />
                    <div style={{ marginTop: 16 }}>
                        <Text type="secondary">CSVをアップロード中です。しばらくお待ちください。</Text>
                    </div>
                </div>
            </Modal>
        </>
    );
};

export default UploadDatabasePage;
