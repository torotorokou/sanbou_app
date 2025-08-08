// /app/src/pages/report/InteractiveApiDemo.tsx

/**
 * インタラクティブAPI通信デモページ
 * 
 * 🎯 目的：
 * - 最適化されたAPI通信フローの動作確認
 * - 新しいインタラクティブAPIサービスの実証
 * - 段階的API通信（start → update → complete）のテスト
 */

import React, { useState } from 'react';
import { Card, Button, Steps, Alert, Space, Typography, Divider } from 'antd';
import { useReportModeManager } from '../../hooks/report/useReportModeManager';
import ReportModeBase from '../../components/Report/ReportModeBase';
import { INTERACTIVE_STEPS } from '../../pages/types/interactiveMode';
import type { ReportKey } from '../../constants/reportConfig';

const { Title, Paragraph, Text } = Typography;
const { Step } = Steps;

// ==============================
// 🎮 デモページコンポーネント
// ==============================

const InteractiveApiDemo: React.FC = () => {
    const [selectedReportKey, setSelectedReportKey] = useState<ReportKey>('block_unit_price');

    // 最適化されたフックを使用
    const reportManager = useReportModeManager({
        initialReportKey: selectedReportKey,
        onModeChange: (mode) => {
            console.log('Mode changed to:', mode);
        },
        onInteractiveStepChange: (step) => {
            console.log('Interactive step changed to:', step);
        },
    });

    // ==============================
    // 🎨 レンダリング関数
    // ==============================

    /**
     * API通信フロー状況の表示
     */
    const renderApiFlowStatus = () => {
        const { interactiveState, isInteractiveMode } = reportManager;

        if (!isInteractiveMode) {
            return (
                <Alert
                    message="自動モード"
                    description="選択されたレポートは自動モードです。従来のAPI通信方式を使用します。"
                    type="info"
                    style={{ marginBottom: '24px' }}
                />
            );
        }

        const currentStepIndex = Object.values(INTERACTIVE_STEPS).indexOf(interactiveState.currentStep);

        return (
            <Card title="インタラクティブAPI通信フロー" style={{ marginBottom: '24px' }}>
                <Steps current={currentStepIndex} size="small">
                    <Step title="初期化" description="start API" />
                    <Step title="データ処理" description="処理実行" />
                    <Step title="ユーザー入力" description="パラメータ設定" />
                    <Step title="更新処理" description="update API" />
                    <Step title="完了処理" description="complete API" />
                </Steps>

                <Divider />

                <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                        <Text strong>現在のステップ:</Text> {interactiveState.currentStep}
                    </div>
                    <div>
                        <Text strong>ローディング状態:</Text> {interactiveState.isLoading ? '処理中' : '待機中'}
                    </div>
                    {interactiveState.error && (
                        <Alert
                            message="エラー"
                            description={interactiveState.error}
                            type="error"
                        />
                    )}
                    {interactiveState.interactions && (
                        <div>
                            <Text strong>インタラクション数:</Text> {Array.isArray(interactiveState.interactions) ? interactiveState.interactions.length : 0}
                        </div>
                    )}
                </Space>
            </Card>
        );
    };

    /**
     * レポートタイプ選択UI
     */
    const renderReportSelector = () => {
        const reportOptions = [
            { key: 'block_unit_price', label: '街区別単価レポート (インタラクティブ)', isInteractive: true },
            { key: 'factory_report', label: '工場レポート (自動)', isInteractive: false },
        ];

        return (
            <Card title="レポートタイプ選択" style={{ marginBottom: '24px' }}>
                <Space wrap>
                    {reportOptions.map((option) => (
                        <Button
                            key={option.key}
                            type={selectedReportKey === option.key ? 'primary' : 'default'}
                            onClick={() => {
                                setSelectedReportKey(option.key as ReportKey);
                                reportManager.changeReport(option.key);
                            }}
                            style={{
                                borderColor: option.isInteractive ? '#1890ff' : '#d9d9d9',
                                backgroundColor: option.isInteractive && selectedReportKey === option.key ? '#1890ff' : undefined,
                            }}
                        >
                            {option.label}
                        </Button>
                    ))}
                </Space>
            </Card>
        );
    };

    /**
     * API通信ログの表示
     */
    const renderApiLog = () => {
        return (
            <Card title="API通信ログ" style={{ marginBottom: '24px' }}>
                <Paragraph>
                    <Text code>
                        このセクションでは実際のAPI通信の流れをリアルタイムで確認できます。
                        開発者ツールのNetworkタブでAPIリクエストの詳細を確認してください。
                    </Text>
                </Paragraph>

                <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                        <Text strong>期待されるAPI呼び出し順序:</Text>
                    </div>
                    <ol style={{ paddingLeft: '20px' }}>
                        <li><Text code>POST /ledger_api/report/interactive/start</Text> - セッション開始</li>
                        <li><Text code>POST /ledger_api/report/interactive/update</Text> - ユーザー入力送信</li>
                        <li><Text code>POST /ledger_api/report/interactive/complete</Text> - 処理完了</li>
                    </ol>
                </Space>
            </Card>
        );
    };

    // ==============================
    // 🎯 メインレンダリング
    // ==============================

    return (
        <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
            <Title level={2}>
                🚀 インタラクティブAPI通信デモ
            </Title>

            <Paragraph>
                このページでは、最適化されたインタラクティブAPI通信システムの動作を確認できます。
                インタラクティブモードのレポートでは、段階的なAPI通信により効率的な処理を実現します。
            </Paragraph>

            <Divider />

            {/* レポートタイプ選択 */}
            {renderReportSelector()}

            {/* API通信フロー状況 */}
            {renderApiFlowStatus()}

            {/* API通信ログ */}
            {renderApiLog()}

            {/* メインのレポートコンポーネント */}
            <Card title="レポート生成インターフェース">
                <ReportModeBase
                    step={{
                        steps: ['初期化', '処理中', '完了'],
                        currentStep: reportManager.currentStep,
                        setCurrentStep: reportManager.setCurrentStep,
                    }}
                    file={{
                        csvConfigs: (reportManager.selectedConfig as any)?.csvConfigs || [],
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
            </Card>

            {/* デバッグ情報 */}
            <Card title="デバッグ情報" style={{ marginTop: '24px' }}>
                <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                        <Text strong>選択レポート:</Text> {reportManager.selectedReport}
                    </div>
                    <div>
                        <Text strong>モード:</Text> {reportManager.modeInfo.mode}
                    </div>
                    <div>
                        <Text strong>インタラクティブモード:</Text> {reportManager.isInteractiveMode ? 'Yes' : 'No'}
                    </div>
                    <div>
                        <Text strong>必須CSV確認:</Text> {reportManager.areRequiredCsvsUploaded() ? 'OK' : 'NG'}
                    </div>
                </Space>
            </Card>
        </div>
    );
};

export default InteractiveApiDemo;
