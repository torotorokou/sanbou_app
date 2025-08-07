import React from 'react';
import { Modal, Steps, Button } from 'antd';
import type { ReactNode } from 'react';

const { Step } = Steps;

// 型定義をローカルで定義
export type ModalStepConfig = {
    label: string;
    content: React.ReactNode;
    showNext?: boolean;
    showPrev?: boolean;
    showClose?: boolean;
};

export type ReportStepperModalProps = {
    open: boolean;
    steps: string[];
    currentStep: number;
    onNext: () => void;
    onPrev?: () => void;
    onClose?: () => void;
    children: ReactNode;
    stepConfigs: ModalStepConfig[];
    isInteractive?: boolean; // インタラクティブモードフラグ
    allowEarlyClose?: boolean; // 途中での閉じる操作を許可するか
};

const ReportStepperModal: React.FC<ReportStepperModalProps> = ({
    open,
    steps,
    currentStep,
    onNext,
    onPrev,
    onClose,
    children,
    stepConfigs,
    isInteractive = false,
    allowEarlyClose = true
}) => {
    // stepConfigsが未定義や空の場合、currentStepが範囲外の場合は何も表示しない
    if (!stepConfigs || stepConfigs.length === 0 || currentStep < 0 || currentStep >= stepConfigs.length) {
        return null;
    }
    const config = stepConfigs[currentStep] || {};

    // インタラクティブモードでの閉じる制御
    const shouldAllowClose = isInteractive ? allowEarlyClose || config.showClose : true;
    const shouldShowSystemClose = !isInteractive || allowEarlyClose; // ×ボタンとESCキーの制御
    const handleModalClose = shouldAllowClose ? onClose : undefined;

    return (
        <Modal
            open={open}
            onCancel={shouldShowSystemClose ? onClose : undefined}
            footer={null}
            centered
            width={720}
            closable={shouldShowSystemClose}
            keyboard={shouldShowSystemClose} // ESCキーでの閉じる操作を制御
            maskClosable={shouldShowSystemClose} // マスククリックでの閉じる操作を制御
        >
            <Steps current={currentStep} style={{ marginBottom: 24, marginTop: 16 }}>
                {steps.map((title, idx) => (
                    <Step key={idx} title={title} />
                ))}
            </Steps>

            <div style={{ minHeight: 240 }}>{children}</div>

            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 24 }}>
                <div>
                    {config.showPrev && (
                        <Button onClick={onPrev}>
                            戻る
                        </Button>
                    )}
                </div>
                <div>
                    {config.showNext && (
                        <Button type="primary" onClick={onNext} style={{ marginRight: 8 }}>
                            次へ
                        </Button>
                    )}
                    {config.showClose && (
                        <Button type="primary" onClick={onClose}>
                            閉じる
                        </Button>
                    )}
                    {/* インタラクティブモードで途中終了が必要な場合の緊急閉じるボタン */}
                    {isInteractive && !config.showClose && (
                        <Button onClick={onClose} style={{ marginLeft: 8 }}>
                            終了
                        </Button>
                    )}
                </div>
            </div>
        </Modal>
    );
};

export default ReportStepperModal;
