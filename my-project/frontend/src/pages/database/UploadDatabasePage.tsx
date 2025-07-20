import React from 'react';
import { Row, Col, Button, message } from 'antd';
import CsvUploadPanel from '@/components/database/CsvUploadPanel';
import { CsvPreviewCard } from '@/components/database/CsvPreviewCard';
import {
    UPLOAD_CSV_TYPES,
    UPLOAD_CSV_DEFINITIONS,
} from '@/constants/uploadCsvConfig';
import { useCsvUploadArea } from '@/hooks/database/useCsvUploadArea';

const CARD_HEIGHT = 300;
const TABLE_BODY_HEIGHT = 200;

const UploadDatabasePage: React.FC = () => {
    const {
        files,
        validationResults,
        csvPreviews,
        canUpload,
        handleCsvFile,
        removeCsvFile,
    } = useCsvUploadArea();

    const panelFiles = UPLOAD_CSV_TYPES.map((type) => ({
        label: UPLOAD_CSV_DEFINITIONS[type].label,
        file: files[type],
        required: UPLOAD_CSV_DEFINITIONS[type].required,
        onChange: (f: File | null) =>
            f && handleCsvFile(UPLOAD_CSV_DEFINITIONS[type].label, f),
        validationResult: validationResults[type],
        onRemove: () => removeCsvFile(type),
    }));

    // アップロード処理
    const handleUpload = async () => {
        const formData = new FormData();
        Object.entries(files).forEach(([type, file]) => {
            if (file) formData.append(type, file);
        });

        let res: Response;
        let result: any;

        try {
            res = await fetch('/sql_api/upload/syogun_csv', {
                method: 'POST',
                body: formData,
            });
            // レスポンスの中身（ステータスとbody）を必ず一度出力
            console.log("res.status", res.status);
            const text = await res.text();
            console.log("res.text", text);

            try {
                result = JSON.parse(text);
            } catch {
                message.error('サーバー応答がJSONではありません: ' + text);
                return;
            }

            if (res.ok && result.status === "success") {
                message.success(result.message ?? 'アップロード成功');
            } else {
                message.error(result?.message ?? 'アップロード失敗');
            }
        } catch (err) {
            message.error('サーバーに接続できませんでした。');
        }
    };
    return (
        <Row style={{ height: '100vh', minHeight: 600 }}>
            {/* 左: アップロード＋ボタン */}
            <Col
                span={8}
                style={{
                    padding: 16,
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                }}
            >
                <CsvUploadPanel
                    upload={{
                        files: panelFiles,
                        makeUploadProps: (label, onChange) => ({
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
                    type='primary'
                    disabled={!canUpload}
                    onClick={handleUpload}
                    style={{ marginTop: 24, width: '100%' }}
                >
                    アップロードする
                </Button>
            </Col>
            {/* 右: プレビュー */}
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
                {UPLOAD_CSV_TYPES.map((type) => (
                    <CsvPreviewCard
                        key={type}
                        type={type}
                        csvPreview={csvPreviews[type]}
                        validationResult={validationResults[type]}
                        cardHeight={CARD_HEIGHT}
                        tableBodyHeight={TABLE_BODY_HEIGHT}
                    />
                ))}
            </Col>
        </Row>
    );
};

export default UploadDatabasePage;
