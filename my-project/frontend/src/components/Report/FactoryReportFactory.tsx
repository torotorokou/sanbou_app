// /app/src/components/Report/FactoryReportFactory.tsx
import React, { useState, useCallback } from 'react';
import { Row, Col, Card, Button, Upload, message, Space, Tag } from 'antd';
import { UploadOutlined, FileExcelOutlined, FilePdfOutlined, EyeOutlined } from '@ant-design/icons';
import type { UploadChangeParam } from 'antd/es/upload';
import type {
    FactoryReportKey,
    FactoryCsvConfigGroup
} from '../../constants/reportConfig/factoryReportConfig';
import {
    getFactoryReportType,
    factoryReportApiUrlMap,
    factoryPdfGeneratorMap,
    factoryPdfPreviewMap
} from '../../constants/reportConfig/factoryReportConfig';

interface FactoryReportFactoryProps {
    reportKey: FactoryReportKey;
    csvConfigs: FactoryCsvConfigGroup;
    onUpload?: (files: File[]) => void;
    onValidationChange?: (results: Record<string, 'valid' | 'invalid' | 'unknown'>) => void;
    getValidationResult?: (label: string) => 'valid' | 'invalid' | 'unknown';
}

/**
 * 工場帳簿専用ファクトリーコンポーネント
 * 
 * 🎯 機能：
 * - 工場帳簿専用CSV処理
 * - 自動/インタラクティブ判定
 * - バックエンド連携
 * - エクセル/PDF/プレビュー機能
 */
const FactoryReportFactory: React.FC<FactoryReportFactoryProps> = ({
    reportKey,
    csvConfigs,
    onUpload,
    onValidationChange,
    getValidationResult,
}) => {
    const [csvFiles, setCsvFiles] = useState<File[]>([]);
    const [isProcessing, setIsProcessing] = useState(false);
    const [reportResult, setReportResult] = useState<{
        reportKey: string;
        type: string;
        files: number;
        generatedAt: string;
        excelUrl: string;
        pdfUrl: string;
    } | null>(null);

    const reportType = getFactoryReportType(reportKey);
    const apiUrl = factoryReportApiUrlMap[reportKey];
    const pdfGenerator = factoryPdfGeneratorMap[reportKey];
    const previewImage = factoryPdfPreviewMap[reportKey];

    // ファイルアップロードハンドラー
    const handleFileChange = useCallback((info: UploadChangeParam) => {
        const fileList = info.fileList.map((file) => file.originFileObj || file).filter(Boolean) as File[];
        setCsvFiles(fileList);
        onUpload?.(fileList);

        // 簡易バリデーション（実際はより詳細な処理）
        const validationResults: Record<string, 'valid' | 'invalid' | 'unknown'> = {};
        csvConfigs.forEach(config => {
            const hasMatchingFile = fileList.some(file =>
                file.name.toLowerCase().includes(config.config.label.toLowerCase()) ||
                file.name.toLowerCase().includes(config.config.type)
            );
            validationResults[config.config.label] = hasMatchingFile ? 'valid' : 'unknown';
        });
        onValidationChange?.(validationResults);
    }, [csvConfigs, onUpload, onValidationChange]);

    // 帳簿生成開始
    const handleGenerateReport = useCallback(async () => {
        if (csvFiles.length === 0) {
            message.warning('CSVファイルを選択してください');
            return;
        }

        // 必須ファイルチェック
        const requiredConfigs = csvConfigs.filter(config => config.required);
        const missingRequired = requiredConfigs.some(config => {
            const hasFile = csvFiles.some(file =>
                file.name.toLowerCase().includes(config.config.label.toLowerCase())
            );
            return !hasFile;
        });

        if (missingRequired) {
            message.error('必須CSVファイルが不足しています');
            return;
        }

        setIsProcessing(true);

        try {
            // バックエンド連携（実際のAPI呼び出し）
            console.log(`Generating factory report: ${reportKey}`);
            console.log(`API URL: ${apiUrl}`);
            console.log(`Report Type: ${reportType}`);
            console.log('CSV Files:', csvFiles.map(f => f.name));

            // 模擬API処理
            await new Promise(resolve => setTimeout(resolve, 2000));

            const mockResult = {
                reportKey,
                type: reportType,
                files: csvFiles.length,
                generatedAt: new Date().toISOString(),
                excelUrl: `/factory/excel/${reportKey}_${Date.now()}.xlsx`,
                pdfUrl: await pdfGenerator(),
            };

            setReportResult(mockResult);
            message.success(`${reportType === 'auto' ? '自動' : 'インタラクティブ'}帳簿が正常に生成されました！`);

        } catch (error) {
            console.error('Factory report generation error:', error);
            message.error('帳簿生成中にエラーが発生しました');
        } finally {
            setIsProcessing(false);
        }
    }, [csvFiles, csvConfigs, reportKey, apiUrl, reportType, pdfGenerator]);

    // エクセルダウンロード
    const handleDownloadExcel = useCallback(() => {
        if (reportResult) {
            window.open(reportResult.excelUrl, '_blank');
        }
    }, [reportResult]);

    // PDF印刷
    const handlePrintPdf = useCallback(() => {
        if (reportResult) {
            window.open(reportResult.pdfUrl, '_blank');
        }
    }, [reportResult]);

    // プレビュー表示
    const handleShowPreview = useCallback(() => {
        window.open(previewImage, '_blank');
    }, [previewImage]);

    return (
        <div style={{ padding: '16px' }}>
            <Row gutter={[16, 16]}>
                {/* CSV アップロードエリア */}
                <Col span={24}>
                    <Card title={`📁 ${reportKey} 用CSVファイル`}>
                        <div style={{ marginBottom: 16 }}>
                            <Space wrap>
                                <Tag color="blue">帳簿タイプ: {reportType === 'auto' ? '自動生成' : 'インタラクティブ'}</Tag>
                                <Tag color="green">必要ファイル数: {csvConfigs.filter(c => c.required).length}</Tag>
                                <Tag color="orange">任意ファイル数: {csvConfigs.filter(c => !c.required).length}</Tag>
                            </Space>
                        </div>

                        <div style={{ marginBottom: 16 }}>
                            <p><strong>必要なCSVファイル:</strong></p>
                            <ul>
                                {csvConfigs.map((config, index) => {
                                    const validationStatus = getValidationResult?.(config.config.label) || 'unknown';
                                    return (
                                        <li key={index} style={{ marginBottom: 4 }}>
                                            <Space>
                                                <span>{config.config.label}</span>
                                                <Tag color={config.required ? 'red' : 'green'}>
                                                    {config.required ? '必須' : '任意'}
                                                </Tag>
                                                <Tag color={
                                                    validationStatus === 'valid' ? 'green' :
                                                        validationStatus === 'invalid' ? 'red' : 'default'
                                                }>
                                                    {validationStatus === 'valid' ? '✓' :
                                                        validationStatus === 'invalid' ? '✗' : '?'}
                                                </Tag>
                                            </Space>
                                        </li>
                                    );
                                })}
                            </ul>
                        </div>

                        <Upload
                            multiple
                            accept=".csv"
                            beforeUpload={() => false}
                            onChange={handleFileChange}
                            showUploadList={{ showRemoveIcon: true }}
                        >
                            <Button icon={<UploadOutlined />} size="large">
                                CSVファイルを選択
                            </Button>
                        </Upload>

                        {csvFiles.length > 0 && (
                            <div style={{ marginTop: 16 }}>
                                <p><strong>選択済みファイル: {csvFiles.length}個</strong></p>
                                <ul>
                                    {csvFiles.map((file, index) => (
                                        <li key={index}>{file.name}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </Card>
                </Col>

                {/* 帳簿生成ボタン */}
                <Col span={24}>
                    <Card>
                        <div style={{ textAlign: 'center' }}>
                            <Button
                                type="primary"
                                size="large"
                                loading={isProcessing}
                                disabled={csvFiles.length === 0}
                                onClick={handleGenerateReport}
                                style={{ minWidth: 200 }}
                            >
                                🏭 {reportType === 'auto' ? '自動' : 'インタラクティブ'}帳簿生成
                            </Button>
                        </div>
                    </Card>
                </Col>

                {/* 結果表示・操作エリア */}
                {reportResult && (
                    <Col span={24}>
                        <Card title="📊 帳簿生成結果">
                            <div style={{ textAlign: 'center' }}>
                                <Space size="large">
                                    <Button
                                        type="primary"
                                        icon={<FileExcelOutlined />}
                                        onClick={handleDownloadExcel}
                                        size="large"
                                    >
                                        エクセルダウンロード
                                    </Button>
                                    <Button
                                        icon={<FilePdfOutlined />}
                                        onClick={handlePrintPdf}
                                        size="large"
                                    >
                                        PDF印刷
                                    </Button>
                                    <Button
                                        icon={<EyeOutlined />}
                                        onClick={handleShowPreview}
                                        size="large"
                                    >
                                        プレビュー
                                    </Button>
                                </Space>
                            </div>

                            <div style={{ marginTop: 16, fontSize: '12px', color: '#666', textAlign: 'center' }}>
                                生成完了: {new Date().toLocaleString('ja-JP')}
                            </div>
                        </Card>
                    </Col>
                )}
            </Row>
        </div>
    );
};

export default FactoryReportFactory;
