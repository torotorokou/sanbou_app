import React from 'react';
import { Modal, Steps, Button } from 'antd';
import type { ReactNode } from 'react';
import { useWindowSize } from '@/hooks/ui';

const { Step } = Steps;

import type { ModalStepConfig } from '@/constants/reportConfig';

export type ReportStepperModalProps = {
    open: boolean;
    steps: string[];
    currentStep: number;
    onNext: () => void;
    onClose?: () => void;
    children: ReactNode;
    stepConfigs: ModalStepConfig[];
};

const ReportStepperModal: React.FC<ReportStepperModalProps> = ({
    open,
    steps,
    currentStep,
    onNext,
    onClose,
    children,
    stepConfigs,
}) => {
    const { isMobile, isTablet } = useWindowSize();
    const modalWidth = isMobile ? '95vw' : isTablet ? 640 : 720;
    // stepConfigsが未定義や空の場合、currentStepが範囲外の場合は何も表示しない
    if (!stepConfigs || stepConfigs.length === 0 || currentStep < 0 || currentStep >= stepConfigs.length) {
        return null;
    }
    const config = stepConfigs[currentStep] || {};

    return (
        <Modal
            open={open}
            onCancel={onClose}
            footer={null}
            centered
            width={modalWidth}
            closable={false}
        >
            <Steps current={currentStep} style={{ marginBottom: 24 }}>
                {steps.map((title, idx) => (
                    <Step key={idx} title={title} />
                ))}
            </Steps>

            <div style={{ minHeight: 240 }}>{children}</div>

            <div style={{ textAlign: 'right', marginTop: 24 }}>
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
            </div>
        </Modal>
    );
};

export default ReportStepperModal;
