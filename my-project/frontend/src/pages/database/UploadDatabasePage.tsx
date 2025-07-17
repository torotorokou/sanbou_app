// /app/crs / pages / database / UploadDatabasePage.tsx;

import React from 'react';
import { Row, Col, Button } from 'antd';
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

    const handleUpload = async () => {
        // 1. FormDataを生成
        const formData = new FormData();
        // ファイルがあるものだけ追加
        Object.entries(files).forEach(([type, file]) => {
            if (file) {
                formData.append(type, file); // typeをkeyに
            }
        });

        try {
            // 2. fetchでAPIに送信
            const res = await fetch('/api/upload_csv', {
                method: 'POST',
                body: formData,
            });

            if (res.ok) {
                // 3. 成功時の処理（例：アラート表示や画面リセットなど）
                alert('アップロード成功');
            } else {
                // 4. 失敗時
                const msg = await res.text();
                alert('アップロード失敗: ' + msg);
            }
        } catch (err) {
            alert('ネットワークエラー: ' + err);
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
