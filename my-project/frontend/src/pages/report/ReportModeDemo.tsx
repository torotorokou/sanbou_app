// /app/src/pages/report/ReportModeDemo.tsx

/**
 * モード対応レポートシステムのデモンストレーションページ
 * 
 * 🎯 目的：
 * - 自動・インタラクティブモードの動作確認
 * - 実装したアーキテクチャの動作デモ
 * - SOLID原則とMVC構造の実装例
 */

import React, { useState } from 'react';
import { Card, Row, Col, Typography, Divider, Alert, Space, Tag } from 'antd';
import ReportModeBase from '../../components/Report/ReportModeBase';
import ReportHeader from '../../components/Report/common/ReportHeader';
import { useReportModeManager } from '../../hooks/report/useReportModeManager';
import { getReportModeInfo, getInteractiveReportKeys, getAutoReportKeys } from '../../pages/types/reportMode';
import type { ReportKey } from '../../constants/reportConfig';

const { Title, Paragraph, Text } = Typography;

/**
 * デモンストレーションページ
 */
const ReportModeDemo: React.FC = () => {
    const [selectedDemoKey, setSelectedDemoKey] = useState<ReportKey>('factory_report');

    // モード対応レポート管理フック
    const reportManager = useReportModeManager({
        initialReportKey: selectedDemoKey,
        onModeChange: (mode) => {
            console.log(`🔄 Mode changed to: ${mode}`);
        },
        onInteractiveStepChange: (step) => {
            console.log(`📈 Interactive step changed to: ${step}`);
        },
    });

    // 現在のモード情報
    const modeInfo = getReportModeInfo(selectedDemoKey);
    const interactiveKeys = getInteractiveReportKeys();
    const autoKeys = getAutoReportKeys();

    // ==============================
    // 🎮 イベントハンドラー
    // ==============================

    const handleChangeReportKey = (reportKey: string) => {
        const newKey = reportKey as ReportKey;
        setSelectedDemoKey(newKey);
        reportManager.changeReport(reportKey);
    };

    // 型安全なconfig取得
    const selectedConfig = reportManager.selectedConfig as {
        steps?: string[];
        csvConfigs?: Array<{
            config: { label: string; onParse: (csvText: string) => void };
            required: boolean;
        }>;
    };

    // ==============================
    // 🎨 レンダリング
    // ==============================

    return (
        <div style={{ padding: '24px' }}>
            {/* ヘッダー情報 */}
            <Card style={{ marginBottom: '24px' }}>
                <Title level={2}>📊 モード対応レポートシステム デモ</Title>
                <Paragraph>
                    このページでは、自動帳簿生成とインタラクティブ帳簿生成の両方に対応した
                    新しいレポートシステムの動作を確認できます。
                </Paragraph>
                
                <Row gutter={[16, 16]}>
                    <Col span={12}>
                        <Card size="small" title="🤖 自動モード対応帳票">
                            <Space direction="vertical" style={{ width: '100%' }}>
                                {autoKeys.map(key => (
                                    <Tag key={key} color="blue">{key}</Tag>
                                ))}
                            </Space>
                        </Card>
                    </Col>
                    <Col span={12}>
                        <Card size="small" title="🎮 インタラクティブモード対応帳票">
                            <Space direction="vertical" style={{ width: '100%' }}>
                                {interactiveKeys.map(key => (
                                    <Tag key={key} color="orange">{key}</Tag>
                                ))}
                            </Space>
                        </Card>
                    </Col>
                </Row>
            </Card>

            {/* 現在のモード情報 */}
            <Card style={{ marginBottom: '24px' }}>
                <Title level={4}>🔍 現在の選択状況</Title>
                <Row gutter={[16, 8]}>
                    <Col span={8}>
                        <Text strong>選択中の帳票:</Text> {selectedDemoKey}
                    </Col>
                    <Col span={8}>
                        <Text strong>動作モード:</Text>{' '}
                        <Tag color={modeInfo.isInteractive ? 'orange' : 'blue'}>
                            {modeInfo.isInteractive ? 'インタラクティブ' : '自動'}
                        </Tag>
                    </Col>
                    <Col span={8}>
                        <Text strong>現在のステップ:</Text> {reportManager.currentStep}
                    </Col>
                </Row>
                
                {modeInfo.isInteractive && (
                    <Alert
                        style={{ marginTop: '16px' }}
                        message="インタラクティブモード"
                        description="この帳票はユーザーの入力を必要とする処理を含みます。生成時にパラメータの設定が求められます。"
                        type="info"
                        showIcon
                    />
                )}
            </Card>

            <Divider />

            {/* メインレポートシステム */}
            <ReportHeader
                reportKey={reportManager.selectedReport}
                onChangeReportKey={handleChangeReportKey}
                currentStep={reportManager.currentStep}
                pageGroup="all"
            />

            <ReportModeBase
                step={{
                    steps: selectedConfig.steps || [],
                    currentStep: reportManager.currentStep,
                    setCurrentStep: reportManager.setCurrentStep,
                }}
                file={{
                    csvConfigs: (selectedConfig.csvConfigs || []) as Array<{
                        config: { label: string; onParse: (csvText: string) => void };
                        required: boolean;
                    }>,
                    files: reportManager.csvFiles,
                    onUploadFile: reportManager.uploadCsvFile,
                }}
                preview={{
                    previewUrl: reportManager.previewUrl,
                    setPreviewUrl: reportManager.setPreviewUrl,
                }}
                modal={{
                    modalOpen: reportManager.isModalOpen,
                    setModalOpen: reportManager.setIsModalOpen,
                }}
                finalized={{
                    finalized: reportManager.isFinalized,
                    setFinalized: reportManager.setIsFinalized,
                }}
                loading={{
                    loading: reportManager.isLoading,
                    setLoading: reportManager.setIsLoading,
                }}
                reportKey={reportManager.selectedReport}
                onContinueInteractive={reportManager.continueInteractiveProcess}
                onResetInteractive={reportManager.resetInteractiveState}
                interactiveState={reportManager.interactiveState}
            />

            {/* 開発者向け情報 */}
            <Card style={{ marginTop: '24px' }} title="🛠️ 開発者情報">
                <Row gutter={[16, 16]}>
                    <Col span={12}>
                        <Title level={5}>🏗️ アーキテクチャ特徴</Title>
                        <ul>
                            <li><strong>SOLID原則準拠:</strong> 単一責任、開放閉鎖原則</li>
                            <li><strong>MVC構造:</strong> ビジネスロジック分離</li>
                            <li><strong>型安全性:</strong> TypeScript完全対応</li>
                            <li><strong>拡張性:</strong> 新モード追加が容易</li>
                        </ul>
                    </Col>
                    <Col span={12}>
                        <Title level={5}>🔧 技術スタック</Title>
                        <ul>
                            <li><strong>状態管理:</strong> useReportModeManager</li>
                            <li><strong>サービス層:</strong> ReportModeService</li>
                            <li><strong>UI層:</strong> ReportModeBase</li>
                            <li><strong>型定義:</strong> pages/types/*</li>
                        </ul>
                    </Col>
                </Row>
            </Card>
        </div>
    );
};

export default ReportModeDemo;
