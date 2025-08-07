// /app/src/pages/report/GenericReportPage.tsx
import React, { useState } from 'react';
import { Card, Row, Col, Button, Upload, message } from 'antd';
import { UploadOutlined } from '@ant-design/icons';

import { GenericReportSelector } from '../../components/Report/common/GenericReportSelector';
import { GenericReportFactory } from '../../components/Report/GenericReportFactory';
import { useReportConfig } from '../../hooks/useReportConfig';
import type { UploadChangeParam } from 'antd/es/upload';
import type { ReportConfigPackage } from '../../types/reportConfig';

interface GenericReportPageProps {
    config: ReportConfigPackage;
    title?: string;
    description?: string;
}

/**
 * 汎用的な帳票作成ページコンポーネント
 * 
 * どの帳票設定パッケージでも使用可能な汎用ページ
 * 例：管理系帳票、工場系帳票、顧客系帳票など
 */
export const GenericReportPage: React.FC<GenericReportPageProps> = ({
    config,
    title,
    description,
}) => {
    const reportConfig = useReportConfig(config);
    const [selectedReportKey, setSelectedReportKey] = useState<string>();
    const [csvFiles, setCsvFiles] = useState<File[]>([]);
    const [showModal, setShowModal] = useState(false);

    // 帳票タイプ変更ハンドラー
    const handleReportChange = (reportKey: string) => {
        setSelectedReportKey(reportKey);
        setCsvFiles([]); // ファイルリセット
    };

    // ファイルアップロードハンドラー
    const handleFileChange = (info: UploadChangeParam) => {
        const fileList = info.fileList.map((file) => file.originFileObj || file).filter(Boolean) as File[];
        setCsvFiles(fileList);
    };

    // CSV生成ボタンハンドラー
    const handleGenerateReport = () => {
        if (!selectedReportKey || csvFiles.length === 0) {
            message.warning('帳票タイプを選択し、CSVファイルをアップロードしてください');
            return;
        }
        setShowModal(true);
    };

    // モーダル完了ハンドラー
    const handleReportComplete = (result: unknown) => {
        console.log(`[${config.name}] Report completed:`, result);
        setShowModal(false);
    };

    // モーダルエラーハンドラー
    const handleReportError = (error: string) => {
        console.error(`[${config.name}] Report error:`, error);
        message.error(`エラー: ${error}`);
    };

    const selectedReport = selectedReportKey ? config.reportKeys[selectedReportKey] : null;
    const csvConfig = selectedReportKey ? reportConfig.getCsvConfig(selectedReportKey) : [];

    return (
        <div className="generic-report-page" style={{ padding: '24px' }}>
            <Row gutter={[16, 16]}>
                {/* ページヘッダー */}
                <Col span={24}>
                    <Card>
                        <h1>{title || `${config.name} 帳票作成システム`}</h1>
                        {description && <p>{description}</p>}
                        <div style={{ marginTop: 16 }}>
                            <strong>設定セット:</strong> {config.name} |
                            <strong> 利用可能帳票:</strong> {reportConfig.getReportOptions().length}種類
                        </div>
                    </Card>
                </Col>

                {/* 帳票選択セクション */}
                <Col span={24}>
                    <GenericReportSelector
                        config={config}
                        selectedReportKey={selectedReportKey}
                        onReportChange={handleReportChange}
                    />
                </Col>

                {/* CSVアップロードセクション */}
                {selectedReportKey && (
                    <Col span={24}>
                        <Card title={`${selectedReport?.label} - CSVファイルアップロード`}>
                            <div style={{ marginBottom: 16 }}>
                                <p><strong>必要なCSVファイル:</strong></p>
                                <ul>
                                    {csvConfig.map((cfg, index) => (
                                        <li key={index}>
                                            {cfg.config.label}
                                            <span style={{ color: cfg.required ? 'red' : 'green' }}>
                                                ({cfg.required ? '必須' : '任意'})
                                            </span>
                                        </li>
                                    ))}
                                </ul>
                            </div>

                            <Upload
                                multiple
                                accept=".csv"
                                beforeUpload={() => false} // 自動アップロードを無効化
                                onChange={handleFileChange}
                                showUploadList={{
                                    showRemoveIcon: true,
                                }}
                            >
                                <Button icon={<UploadOutlined />}>CSVファイルを選択</Button>
                            </Upload>

                            <div style={{ marginTop: 16, textAlign: 'center' }}>
                                <Button
                                    type="primary"
                                    size="large"
                                    disabled={csvFiles.length === 0}
                                    onClick={handleGenerateReport}
                                >
                                    {selectedReport?.label}を生成
                                </Button>
                            </div>
                        </Card>
                    </Col>
                )}

                {/* 帳票詳細情報 */}
                {selectedReport && (
                    <Col span={24}>
                        <Card size="small" title="帳票詳細">
                            <Row gutter={[16, 8]}>
                                <Col span={8}>
                                    <strong>帳票名:</strong> {selectedReport.label}
                                </Col>
                                <Col span={8}>
                                    <strong>処理タイプ:</strong> {selectedReport.type === 'auto' ? '自動生成' : 'インタラクティブ'}
                                </Col>
                                <Col span={8}>
                                    <strong>必要ファイル数:</strong> {csvConfig.length}個
                                </Col>
                                <Col span={24}>
                                    <strong>ステップ数:</strong> {selectedReportKey ? reportConfig.getAllModalSteps(selectedReportKey).length : 0}段階
                                </Col>
                            </Row>
                        </Card>
                    </Col>
                )}
            </Row>

            {/* 帳票生成モーダル */}
            {showModal && selectedReportKey && (
                <GenericReportFactory
                    config={config}
                    reportKey={selectedReportKey}
                    csvFiles={csvFiles}
                    onComplete={handleReportComplete}
                    onError={handleReportError}
                    onStepChange={(step) => console.log(`[${config.name}] Step changed:`, step)}
                />
            )}
        </div>
    );
};
