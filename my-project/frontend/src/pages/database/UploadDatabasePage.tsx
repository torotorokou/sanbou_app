import React, { useState } from 'react';
import {
    Row,
    Col,
    Button,
    message,
    notification,
    Collapse,
    Typography,
    Tag,
    List,
    Modal,
    Spin,
} from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';
import CsvUploadPanel from '@/components/database/CsvUploadPanel';
import { CsvPreviewCard } from '@/components/database/CsvPreviewCard';
import {
    UPLOAD_CSV_TYPES,
    UPLOAD_CSV_DEFINITIONS,
} from '@/constants/uploadCsvConfig';
import { useCsvUploadArea } from '@/hooks/database/useCsvUploadArea';

const { Paragraph, Text } = Typography;

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

    const [uploading, setUploading] = useState(false);

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
        const formData = new FormData();
        Object.entries(files).forEach(([type, file]) => {
            if (file) formData.append(type, file);
        });

        const DISPLAY_AFTER_API_MS = 1000;
        let notifyFn = () => { };

        setUploading(true);

        try {
            const res = await fetch('/sql_api/upload/syogun_csv', {
                method: 'POST',
                body: formData,
            });

            const text = await res.text();
            let result: any;
            try {
                result = JSON.parse(text);
            } catch {
                notifyFn = () => {
                    notification.error({
                        message: 'サーバーエラー',
                        description: `サーバー応答がJSONではありません: ${text}`,
                        duration: 6,
                    });
                };
                return;
            }

            if (res.ok && result.status === "success") {
                notifyFn = () => {
                    notification.success({
                        message: 'アップロード成功',
                        description: result.detail ?? 'CSVファイルのアップロードが完了しました。',
                        duration: 4,
                    });
                };
            } else {
                notifyFn = () => {
                    notification.error({
                        message: 'アップロード失敗',
                        description: result?.detail ?? 'アップロード中にエラーが発生しました。',
                        duration: 6,
                    });

                    if (result?.hint) {
                        notification.info({
                            message: 'ヒント',
                            description: result.hint,
                            duration: 6,
                        });
                    }

                    if (result?.result) {
                        Object.entries(result.result).forEach(([key, val]: [string, any]) => {
                            if (val.status === "error") {
                                notification.warning({
                                    message: `[${val.filename ?? key}] のエラー`,
                                    description: val.detail ?? '詳細不明のエラーが発生しました。',
                                    duration: 5,
                                });
                            }
                        });
                    }
                };
            }

            await new Promise((resolve) => setTimeout(resolve, DISPLAY_AFTER_API_MS));
        } catch (err) {
            notifyFn = () => {
                notification.error({
                    message: '接続エラー',
                    description: 'サーバーに接続できませんでした。ネットワークを確認してください。',
                    duration: 6,
                });
            };
        } finally {
            setUploading(false);
            setTimeout(() => {
                notifyFn();
            }, 300);
        }
    };

    return (
        <>
            <Row style={{ height: '100vh', minHeight: 600 }}>
                <Col
                    span={8}
                    style={{
                        padding: 16,
                        height: '100%',
                        display: 'flex',
                        flexDirection: 'column',
                    }}
                >
                    <Collapse
                        defaultActiveKey={[]}
                        style={{
                            marginBottom: 16,
                            backgroundColor: '#f6ffed',
                            border: '1px solid #b7eb8f',
                            borderRadius: 6,
                        }}
                        expandIconPosition="start"
                    >
                        <Collapse.Panel
                            header={
                                <span style={{ fontWeight: 'bold' }}>
                                    <InfoCircleOutlined style={{ marginRight: 8, color: '#52c41a' }} />
                                    アップロード手順・ルール
                                </span>
                            }
                            key="1"
                        >
                            <Paragraph>
                                以下の <Tag color="red">3つのCSVファイル</Tag> をアップロードしてください。
                            </Paragraph>

                            <List
                                size="small"
                                bordered={false}
                                dataSource={[
                                    { name: '受入一覧', required: true },
                                    { name: '出荷一覧', required: true },
                                    { name: 'ヤード一覧', required: true },
                                ]}
                                renderItem={(item) => (
                                    <List.Item style={{ paddingLeft: 0 }}>
                                        <Tag color="blue">{item.name}</Tag>
                                        <Text type="secondary">（必須）</Text>
                                    </List.Item>
                                )}
                                style={{ marginBottom: 12 }}
                            />

                            <Paragraph>
                                <Text type="danger">⚠️ ファイルは「将軍ソフトからダウンロードしたままの状態」でアップロードしてください。</Text><br />
                                自分で編集・加工・列の並び替え・名前変更をしたファイルは使用できません。
                            </Paragraph>

                            <Paragraph>
                                <Text type="warning">📅 アップロードするすべてのファイルで「伝票日付」がそろっている必要があります。</Text><br />
                                1日でもズレているとエラーになりますので、日付の範囲をご確認ください。
                            </Paragraph>
                        </Collapse.Panel>
                    </Collapse>

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