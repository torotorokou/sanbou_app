// /app/src/components/Report/interactive/InteractiveReportModal.tsx

/**
 * インタラクティブレポート生成用モーダル
 * 
 * 🎯 目的：
 * - インタラクティブモードの複雑なUIを専用コンポーネントで管理
 * - ステップベースの処理フローをユーザーフレンドリーに表示
 * - 既存のモーダルシステムとの統合
 */

import React, { useState } from 'react';
import { Modal, Steps, Button, Spin, Alert, Form, Input, Select, Checkbox } from 'antd';
import type {
    InteractiveProcessState,
    InteractiveStep,
    ProcessData
} from '../../../pages/types/interactiveMode';

// ==============================
// 🔧 型定義
// ==============================

interface InteractiveReportModalProps {
    open: boolean;
    onClose: () => void;
    reportName: string;
    state: InteractiveProcessState;
    onContinue?: (userInput: Record<string, unknown>) => void;
    onReset?: () => void;
}

// ==============================
// 🎨 スタイル定数
// ==============================

const MODAL_STYLES = {
    modal: {
        minWidth: '600px',
        maxWidth: '800px',
    },
    stepContainer: {
        margin: '24px 0',
    },
    contentContainer: {
        minHeight: '200px',
        padding: '20px',
        textAlign: 'center' as const,
    },
    buttonContainer: {
        marginTop: '24px',
        textAlign: 'center' as const,
    },
} as const;

// ==============================
// 📋 ステップ設定
// ==============================

const STEP_CONFIGS = [
    { title: '初期化', description: 'データ処理の準備' },
    { title: 'データ処理', description: 'CSVデータの解析' },
    { title: 'ユーザー入力', description: 'パラメータの設定' },
    { title: '計算実行', description: '最終結果の生成' },
    { title: '完了', description: 'レポート作成完了' },
] as const;

// ==============================
// 🎯 メインコンポーネント
// ==============================

const InteractiveReportModal: React.FC<InteractiveReportModalProps> = ({
    open,
    onClose,
    reportName,
    state,
    onContinue,
    onReset,
}) => {

    // ユーザー入力フォームの状態管理
    const [userFormData, setUserFormData] = useState<Record<string, unknown>>({});

    // ==============================
    // 🎨 レンダリング関数
    // ==============================

    /**
     * ステップコンテンツを描画
     */
    const renderStepContent = (): React.ReactNode => {
        const { currentStep, isLoading, error } = state;

        // エラー表示
        if (error) {
            return (
                <div style={MODAL_STYLES.contentContainer}>
                    <Alert
                        message="処理エラー"
                        description={error}
                        type="error"
                        showIcon
                        style={{ marginBottom: '20px' }}
                    />
                    <Button type="primary" onClick={onReset}>
                        最初からやり直す
                    </Button>
                </div>
            );
        }

        // ローディング表示
        if (isLoading) {
            return (
                <div style={MODAL_STYLES.contentContainer}>
                    <Spin size="large" />
                    <p style={{ marginTop: '16px' }}>
                        {getLoadingMessage(currentStep)}
                    </p>
                </div>
            );
        }

        // ステップ別コンテンツ
        switch (currentStep) {
            case -1: // INTERACTIVE_STEPS.INITIAL
                return renderInitialStep();
            case 0: // INTERACTIVE_STEPS.PROCESSING
                return renderProcessingStep();
            case 1: // INTERACTIVE_STEPS.USER_INPUT
                return renderUserInputStep();
            case 2: // INTERACTIVE_STEPS.CALCULATING
                return renderCalculatingStep();
            case 3: // INTERACTIVE_STEPS.COMPLETED
                return renderCompletedStep();
            default:
                return renderUnknownStep();
        }
    };

    /**
     * 初期ステップの表示
     */
    const renderInitialStep = (): React.ReactNode => (
        <div style={MODAL_STYLES.contentContainer}>
            <h3>インタラクティブレポート生成</h3>
            <p>{reportName}を生成します。</p>
            <p>このプロセスでは、途中でパラメータの入力が必要になります。</p>
            <Button type="primary" onClick={() => onContinue?.({})}>
                開始
            </Button>
        </div>
    );

    /**
     * データ処理中ステップの表示
     */
    const renderProcessingStep = (): React.ReactNode => (
        <div style={MODAL_STYLES.contentContainer}>
            <Spin size="large" />
            <h3 style={{ marginTop: '16px' }}>データ処理中</h3>
            <p>アップロードされたCSVファイルを解析しています...</p>
        </div>
    );

    /**
     * ユーザー入力ステップの表示
     */
    const renderUserInputStep = (): React.ReactNode => {
        const { interactions, data } = state;

        return (
            <div style={MODAL_STYLES.contentContainer}>
                <h3>パラメータ設定</h3>
                <p>以下の項目を設定してください：</p>

                {/* 動的フォーム生成 */}
                <Form
                    layout="vertical"
                    onFinish={(values) => {
                        onContinue?.(values);
                    }}
                    initialValues={userFormData}
                    style={{ textAlign: 'left', maxWidth: '400px', margin: '0 auto' }}
                >
                    {renderInteractiveFormItems(interactions, data)}

                    <div style={MODAL_STYLES.buttonContainer}>
                        <Button style={{ marginRight: '8px' }} onClick={onReset}>
                            キャンセル
                        </Button>
                        <Button type="primary" htmlType="submit">
                            次へ
                        </Button>
                    </div>
                </Form>
            </div>
        );
    };

    /**
     * 動的フォーム項目を生成
     */
    const renderInteractiveFormItems = (
        interactions?: unknown[],
        data?: ProcessData
    ): React.ReactNode[] => {
        if (!interactions || !Array.isArray(interactions)) {
            // デフォルトのサンプル項目
            return [
                <Form.Item key="sample" name="sample" label="設定値">
                    <Input placeholder="値を入力してください" />
                </Form.Item>
            ];
        }

        return interactions.map((interaction: any, index: number) => {
            const key = interaction.id || interaction.name || `interaction_${index}`;

            switch (interaction.type) {
                case 'input':
                    return (
                        <Form.Item
                            key={key}
                            name={key}
                            label={interaction.label || interaction.title}
                            rules={interaction.required ? [{ required: true, message: '必須項目です' }] : []}
                        >
                            <Input
                                placeholder={interaction.placeholder || '値を入力'}
                                type={interaction.inputType || 'text'}
                            />
                        </Form.Item>
                    );

                case 'select':
                    return (
                        <Form.Item
                            key={key}
                            name={key}
                            label={interaction.label || interaction.title}
                            rules={interaction.required ? [{ required: true, message: '必須項目です' }] : []}
                        >
                            <Select placeholder={interaction.placeholder || '選択してください'}>
                                {interaction.options?.map((option: any, optIndex: number) => (
                                    <Select.Option
                                        key={option.value || optIndex}
                                        value={option.value}
                                    >
                                        {option.label || option.text || option.value}
                                    </Select.Option>
                                ))}
                            </Select>
                        </Form.Item>
                    );

                case 'checkbox':
                    return (
                        <Form.Item
                            key={key}
                            name={key}
                            valuePropName="checked"
                        >
                            <Checkbox>
                                {interaction.label || interaction.title}
                            </Checkbox>
                        </Form.Item>
                    );

                default:
                    return (
                        <Form.Item key={key} name={key} label={interaction.label || interaction.title}>
                            <Input placeholder="値を入力してください" />
                        </Form.Item>
                    );
            }
        });
    };

    /**
     * 計算実行中ステップの表示
     */
    const renderCalculatingStep = (): React.ReactNode => (
        <div style={MODAL_STYLES.contentContainer}>
            <Spin size="large" />
            <h3 style={{ marginTop: '16px' }}>計算実行中</h3>
            <p>設定されたパラメータで最終計算を行っています...</p>
        </div>
    );

    /**
     * 完了ステップの表示
     */
    const renderCompletedStep = (): React.ReactNode => (
        <div style={MODAL_STYLES.contentContainer}>
            <div style={{ fontSize: '48px', color: '#52c41a', marginBottom: '16px' }}>
                ✅
            </div>
            <h3>完了</h3>
            <p>{reportName}が正常に生成されました！</p>
            <Button type="primary" onClick={onClose}>
                閉じる
            </Button>
        </div>
    );

    /**
     * 不明なステップの表示
     */
    const renderUnknownStep = (): React.ReactNode => (
        <div style={MODAL_STYLES.contentContainer}>
            <Alert
                message="不明なステップ"
                description={`ステップ ${state.currentStep} は対応していません。`}
                type="warning"
                showIcon
            />
            <Button type="primary" onClick={onReset} style={{ marginTop: '16px' }}>
                リセット
            </Button>
        </div>
    );

    // ==============================
    // 🔧 ヘルパー関数
    // ==============================

    /**
     * ローディングメッセージを取得
     */
    const getLoadingMessage = (step: InteractiveStep): string => {
        switch (step) {
            case -1: return '初期化中...';
            case 0: return 'データを処理中...';
            case 1: return 'ユーザー入力を待機中...';
            case 2: return '計算実行中...';
            case 3: return '完了処理中...';
            default: return '処理中...';
        }
    };

    /**
     * 現在のステップインデックスを取得
     */
    const getCurrentStepIndex = (): number => {
        const step = state.currentStep;
        if (step < 0) return 0;
        if (step > 3) return 4;
        return step + 1;
    };

    // ==============================
    // 🎨 レンダリング
    // ==============================

    return (
        <Modal
            title={`インタラクティブレポート生成 - ${reportName}`}
            open={open}
            onCancel={onClose}
            footer={null}
            maskClosable={false}
            style={MODAL_STYLES.modal}
            destroyOnClose
        >
            {/* ステップ表示 */}
            <div style={MODAL_STYLES.stepContainer}>
                <Steps
                    current={getCurrentStepIndex()}
                    size="small"
                    items={STEP_CONFIGS.map(config => ({
                        title: config.title,
                        description: config.description,
                    }))}
                />
            </div>

            {/* メインコンテンツ */}
            {renderStepContent()}
        </Modal>
    );
};

export default InteractiveReportModal;
